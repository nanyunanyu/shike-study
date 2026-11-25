import type { Category, Plan, Task } from '@/types'
import { api } from './client'

export const fetchPlan = () => api<Plan>('/plan')

export const savePlanApi = (base: string, tasks: Task[]) => api<Plan>('/plan', 'PUT', { base, tasks })

export const fetchPlanVersion = (versionId: string) => api<Plan['current']>(`/plan/versions/${versionId}`)

export const saveCategoriesApi = (categories: Category[]) => api<Category[]>('/categories', 'PUT', { categories })
