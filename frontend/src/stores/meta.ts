import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Attribute, ObjectItem } from '@/types'
import * as api from '@/api'

export const useMetaStore = defineStore('meta', () => {
  const attributes = ref<Attribute[]>([])
  const objects = ref<ObjectItem[]>([])
  const loading = ref(false)

  async function fetchAttributes(tableName?: string) {
    loading.value = true
    try {
      const res = await api.listAttributes(tableName)
      attributes.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchObjects() {
    const res = await api.listObjects()
    objects.value = res.data
  }

  async function updateAttribute(id: number, data: any) {
    const res = await api.updateAttribute(id, data)
    const idx = attributes.value.findIndex(a => a.id === id)
    if (idx >= 0) attributes.value[idx] = res.data
  }

  function getObjectList() {
    return objects.value
  }

  return {
    attributes, objects, loading,
    fetchAttributes, fetchObjects, updateAttribute, getObjectList,
  }
})