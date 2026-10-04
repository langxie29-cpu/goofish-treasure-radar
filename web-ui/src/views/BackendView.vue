<script setup lang="ts">
import { ref } from 'vue'
import { backend, saveBackend, checkBackend } from '@/lib/backend'
const input = ref(backend.value)
const error = ref('')
const busy = ref(false)
async function connect() {
  busy.value = true; error.value = ''
  try {
    await saveBackend(input.value)
    await checkBackend()
    window.location.hash = '/dashboard'
    window.location.reload()
  } catch (e) { error.value = e instanceof Error ? e.message : 'Cannot reach Radar backend' }
  finally { busy.value = false }
}
</script>
<template>
  <main class="backend-page">
    <form class="backend-form" @submit.prevent="connect">
      <h1>TREASURE RADAR</h1><p>Android is a client. Keep the backend running on your PC / NAS.</p>
      <label for="backend-url">Backend URL</label>
      <input id="backend-url" v-model="input" type="url" required placeholder="http://192.168.1.20:8000" autocomplete="url" />
      <p v-if="error" role="alert">{{ error }}</p>
      <button :disabled="busy">{{ busy ? 'CONNECTING…' : 'CONNECT' }}</button>
      <RouterLink v-if="backend" to="/dashboard">Back to Dashboard</RouterLink>
    </form>
  </main>
</template>
<style scoped>
.backend-page{min-height:80vh;display:grid;place-items:center;padding:20px}.backend-form{display:grid;gap:18px;width:100%;max-width:420px;overflow-wrap:anywhere}h1{font-size:26px;font-weight:800}input{width:100%;border:1px solid #94a3b8;border-radius:8px;padding:12px;font-size:16px}button{background:#111827;color:white;border-radius:8px;padding:14px;min-height:48px}button:disabled{opacity:.6}[role=alert]{color:#b91c1c}
</style>
