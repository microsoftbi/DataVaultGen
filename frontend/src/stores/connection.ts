import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Connection } from '@/types'
import * as api from '@/api'

export const useConnectionStore = defineStore('connection', () => {
  const connections = ref<Connection[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const res = await api.listConnections()
      connections.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function create(data: any) {
    const res = await api.createConnection(data)
    connections.value.push(res.data)
    return res.data
  }

  async function update(id: number, data: any) {
    const res = await api.updateConnection(id, data)
    const idx = connections.value.findIndex(c => c.id === id)
    if (idx >= 0) connections.value[idx] = res.data
    return res.data
  }

  async function remove(id: number) {
    await api.deleteConnection(id)
    connections.value = connections.value.filter(c => c.id !== id)
  }

  return { connections, loading, fetchAll, create, update, remove }
})