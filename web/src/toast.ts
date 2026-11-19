import { sileo } from 'vue-sileo'

export const toast = {
  success: (title: string, description?: string) =>
    sileo.success({ title, description }),
  error: (title: string, description?: string) =>
    sileo.error({ title, description }),
  info: (title: string, description?: string) =>
    sileo.info({ title, description }),
}