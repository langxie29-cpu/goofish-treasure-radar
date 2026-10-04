<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { backend, nativeClient, checkBackend, apiUrl } from '@/lib/backend'
const online = ref(false), checking = ref(false), today = ref(0), candidates = ref(0)
let timer: ReturnType<typeof setInterval> | undefined
async function refresh() {
  checking.value = true
  try { await checkBackend(); online.value = true }
  catch { online.value = false }
  finally { checking.value = false }
  if (online.value) {
    try {
      const response = await fetch(apiUrl('/api/radar/summary'), { signal: AbortSignal.timeout(6000) })
      if (response.ok) { const data = await response.json(); today.value = data.items_today; candidates.value = data.candidates }
    } catch { /* Statistics failure must not misreport a healthy backend as offline. */ }
  }
}
onMounted(() => { if (nativeClient || backend.value) { refresh(); timer = setInterval(refresh, 30000) } })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
<template>
  <section v-if="nativeClient || backend" class="radar-status">
    <div class="flex flex-wrap justify-between gap-2"><strong>TREASURE RADAR</strong><span :class="online ? 'text-emerald-700' : 'text-red-700'">● {{ checking ? 'CHECKING' : online ? 'ONLINE' : 'OFFLINE' }}</span></div>
    <p class="break-all text-sm">Backend: {{ backend || 'Not configured' }}</p>
    <p v-if="online">Items today (UTC): {{ today }} · Candidates: {{ candidates }}</p>
    <p v-else>Cannot reach Radar backend</p>
    <div class="flex gap-4"><button type="button" :disabled="checking" @click="refresh">RETRY</button><RouterLink to="/backend">SETTINGS</RouterLink></div>
    <nav class="flex flex-wrap gap-4 mt-3"><RouterLink to="/dashboard">Dashboard</RouterLink><RouterLink to="/tasks">Tasks</RouterLink><RouterLink to="/candidates">Candidates</RouterLink><RouterLink to="/settings">Settings</RouterLink></nav>
  </section>
</template>
<style scoped>.radar-status{margin:12px;padding:16px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;display:grid;gap:8px;font-size:14px;overflow-wrap:anywhere}button,a{min-height:44px;display:inline-flex;align-items:center;font-weight:600}</style>
