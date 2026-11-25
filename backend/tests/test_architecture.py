import ast
from pathlib import Path

from study.main import app

STUDY_ROOT = Path(__file__).resolve().parent.parent / 'study'

EXPECTED_API_ROUTES = {
    (('DELETE',), '/api/admin/dispatches/{key}'),
    (('DELETE',), '/api/admin/users/{uid}'),
    (('DELETE',), '/api/admin/users/{uid}/messages/{message_id}'),
    (('DELETE',), '/api/days/{day}/check-in'),
    (('DELETE',), '/api/days/{day}/tasks/{task_id}'),
    (('DELETE',), '/api/messages/{message_id}'),
    (('DELETE',), '/api/milestones/{milestone_id}'),
    (('GET',), '/api/admin/dispatches'),
    (('GET',), '/api/admin/dispatches/{key}'),
    (('GET',), '/api/admin/overview'),
    (('GET',), '/api/admin/users'),
    (('GET',), '/api/admin/users/{uid}/day/{day}'),
    (('GET',), '/api/admin/users/{uid}/messages'),
    (('GET',), '/api/admin/users/{uid}/messages/sent'),
    (('GET',), '/api/admin/users/{uid}/plan'),
    (('GET',), '/api/admin/users/{uid}/statistics'),
    (('GET',), '/api/auth/me'),
    (('GET',), '/api/backup'),
    (('GET',), '/api/days/{day}'),
    (('GET',), '/api/messages'),
    (('GET',), '/api/messages/status'),
    (('GET',), '/api/milestones'),
    (('GET',), '/api/plan'),
    (('GET',), '/api/plan/versions/{version}'),
    (('GET',), '/api/reviews'),
    (('GET',), '/api/statistics'),
    (('GET',), '/api/status'),
    (('GET',), '/api/timer'),
    (('GET',), '/{path:path}'),
    (('POST',), '/api/admin/dispatches'),
    (('POST',), '/api/admin/users'),
    (('POST',), '/api/admin/users/{uid}/messages'),
    (('POST',), '/api/auth/login'),
    (('POST',), '/api/auth/logout'),
    (('POST',), '/api/auth/password'),
    (('POST',), '/api/backup/preview'),
    (('POST',), '/api/days/{day}/check-in'),
    (('POST',), '/api/days/{day}/tasks'),
    (('POST',), '/api/messages/preview'),
    (('POST',), '/api/milestones'),
    (('POST',), '/api/timer/action'),
    (('POST',), '/api/timer/start'),
    (('PUT',), '/api/admin/users/{uid}/active'),
    (('PUT',), '/api/admin/users/{uid}/password'),
    (('PUT',), '/api/backup'),
    (('PUT',), '/api/categories'),
    (('PUT',), '/api/days/{day}/review'),
    (('PUT',), '/api/days/{day}/tasks/{task_id}'),
    (('PUT',), '/api/days/{day}/tasks/{task_id}/done'),
    (('PUT',), '/api/days/{day}/tasks/{task_id}/times'),
    (('PUT',), '/api/messages/{message_id}/read'),
    (('PUT',), '/api/milestones/{milestone_id}'),
    (('PUT',), '/api/plan'),
    (('PUT',), '/api/preferences'),
}


def _imported_roots(tree: ast.AST) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split('.')[0])
    return roots


def _has_sql_execute_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {'execute', 'executemany', 'executescript'}:
                return True
    return False


def _collect_http_routes(routes, prefix: str = '') -> set[tuple[tuple[str, ...], str]]:
    found: set[tuple[tuple[str, ...], str]] = set()
    for route in routes:
        if hasattr(route, 'original_router'):
            sub_prefix = prefix + getattr(route.include_context, 'prefix', '')
            found |= _collect_http_routes(route.original_router.routes, sub_prefix)
        elif getattr(route, 'methods', None):
            methods = tuple(sorted(route.methods - {'HEAD', 'OPTIONS'}))
            found.add((methods, prefix + route.path))
    return found


def test_route_contract_matches_baseline():
    actual = _collect_http_routes(app.routes)
    assert actual == EXPECTED_API_ROUTES


def test_services_layer_is_decoupled_from_fastapi_and_sql():
    for path in (STUDY_ROOT / 'services').glob('*.py'):
        tree = ast.parse(path.read_text())
        imports = _imported_roots(tree)
        assert 'fastapi' not in imports, f'{path.name} 不应依赖 fastapi'
        assert 'starlette' not in imports, f'{path.name} 不应依赖 starlette'
        assert not _has_sql_execute_call(tree), f'{path.name} 不应直接执行 SQL'


def test_routers_layer_has_no_raw_sql():
    for path in (STUDY_ROOT / 'routers').glob('*.py'):
        tree = ast.parse(path.read_text())
        assert not _has_sql_execute_call(tree), f'{path.name} 不应直接执行 SQL'


def test_db_layer_has_no_web_framework_imports():
    for path in (STUDY_ROOT / 'db').rglob('*.py'):
        tree = ast.parse(path.read_text())
        imports = _imported_roots(tree)
        assert 'fastapi' not in imports, f'{path} 不应依赖 fastapi'
        assert 'starlette' not in imports, f'{path} 不应依赖 starlette'


def test_legacy_flat_modules_removed():
    for legacy in ('admin.py', 'extensions.py', 'messages.py', 'models.py', 'reporting.py', 'seed.py', 'store.py', 'timing.py', 'migrations'):
        assert not (STUDY_ROOT / legacy).exists(), f'旧模块残留：{legacy}'
