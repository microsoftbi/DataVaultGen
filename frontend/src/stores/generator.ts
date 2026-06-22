import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGeneratorStore = defineStore('generator', () => {
  const generatedSql = ref('')
  const isGenerating = ref(false)

  return { generatedSql, isGenerating }
})