from .common import Model, Password, Username


class NewUser(Model):
    username: Username
    password: Password
    must_change: bool = True


class ResetPassword(Model):
    password: Password
    must_change: bool = True


class UserActive(Model):
    active: bool
