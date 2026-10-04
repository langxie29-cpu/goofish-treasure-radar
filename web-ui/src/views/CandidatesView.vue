<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/lib/http'
import { apiUrl } from '@/lib/backend'
import { openXianyu } from '@/lib/xianyu'
interface Candidate { item_id: string; title: string; listed_price: number | null; rule_interest_score: number; price_confidence: number; price_type: string; detected_models: {model:string}[]; risk_flags: string[]; evaluation_reason: string; image_urls: string[]; url: string; evaluated_at: string }
const items = ref<Candidate[]>([]), selected = ref<Candidate | null>(null), error = ref(''), loading = ref(false), page = ref(1), total = ref(0), onlyCandidates = ref(true)
async function load(reset = false) {
  if (reset) page.value = 1
  loading.value = true; error.value = ''
  try { const data = await http('/api/radar/candidates', { params: { page: page.value, limit: 20, candidates_only: onlyCandidates.value } }); items.value = data.items; total.value = data.total }
  catch (e) { error.value = e instanceof Error ? e.message : 'Unable to load candidates' }
  finally { loading.value = false }
}
async function open(item: Candidate) { try { await openXianyu(item.url) } catch (e) { error.value = String(e) } }
function next(offset: number) { page.value += offset; load() }
onMounted(() => load())
</script>
<template>
  <section class="candidate-page">
    <header class="flex flex-wrap items-center gap-3"><h1 class="text-2xl font-bold">Candidates</h1><button @click="load(true)">REFRESH</button><label class="flex items-center gap-2"><input v-model="onlyCandidates" type="checkbox" @change="load(true)">Candidates only</label></header>
    <p>Worth opening, not a purchase recommendation. {{ total }} items</p>
    <p v-if="error" role="alert" class="text-red-700 break-all">{{ error }} <button @click="load()">RETRY</button></p>
    <p v-if="loading">Loading…</p><p v-else-if="!items.length && !error">No evaluated items yet. Start a Radar task on your backend.</p>
    <div class="candidate-grid">
      <article v-for="item in items" :key="item.item_id" class="candidate-card">
        <button class="candidate-detail" @click="selected = item">
          <img v-if="item.image_urls[0]" :src="apiUrl(item.image_urls[0])" alt="商品图片" loading="lazy" referrerpolicy="no-referrer" @error="($event.target as HTMLImageElement).hidden = true" />
          <h2>{{ item.title }}</h2><strong>¥{{ item.listed_price ?? '?' }}</strong>
          <p>Interest {{ item.rule_interest_score }}/100 · Price confidence {{ item.price_confidence }}/100</p>
          <p>{{ item.price_type }}</p><p>Models: {{ item.detected_models.map(m => m.model).join(', ') || '—' }}</p>
          <p class="text-amber-800">{{ item.risk_flags.join(' · ') || 'No rule risk flags' }}</p>
          <p>{{ item.evaluation_reason }}</p><span class="text-blue-700">VIEW DETAILS</span>
        </button>
        <button @click="open(item)">OPEN IN XIANYU</button>
      </article>
    </div>
    <footer class="flex flex-wrap gap-4 items-center"><button :disabled="page === 1 || loading" @click="next(-1)">PREVIOUS</button><span>Page {{ page }}</span><button :disabled="page * 20 >= total || loading" @click="next(1)">NEXT</button></footer>
    <div v-if="selected" class="detail-overlay" @click.self="selected = null">
      <section role="dialog" aria-modal="true" aria-label="Candidate details" class="detail-panel">
        <button autofocus @click="selected = null">CLOSE</button><h2 class="text-xl font-bold">{{ selected.title }}</h2>
        <img v-for="image in selected.image_urls" :key="image" :src="apiUrl(image)" alt="商品图片" referrerpolicy="no-referrer" />
        <p>¥{{ selected.listed_price }} · {{ selected.price_type }}</p><p>Interest {{ selected.rule_interest_score }} · Price confidence {{ selected.price_confidence }}</p>
        <p>Models: {{ selected.detected_models.map(m => m.model).join(', ') }}</p><p>{{ selected.risk_flags.join(' · ') }}</p><p>{{ selected.evaluation_reason }}</p><p>{{ selected.evaluated_at }}</p>
        <button @click="open(selected)">OPEN IN XIANYU</button>
      </section>
    </div>
  </section>
</template>
<style scoped>
.candidate-page{display:grid;gap:16px;min-width:0;overflow-wrap:anywhere}.candidate-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:16px}.candidate-card{min-width:0;padding:16px;border:1px solid #cbd5e1;border-radius:12px;background:white;display:grid;gap:12px}.candidate-detail{display:grid;gap:8px;text-align:left;width:100%;padding:0}.candidate-detail h2{font-size:18px;font-weight:700}.candidate-card img{width:100%;height:180px;object-fit:contain;background:#f1f5f9;border-radius:8px}button{min-height:44px;padding:8px;border-radius:8px;font-weight:600}button:disabled{opacity:.4}.candidate-card>button:last-child{background:#111827;color:white}.detail-overlay{position:fixed;inset:0;background:#0008;z-index:150;display:grid;place-items:center;padding:16px}.detail-panel{display:grid;gap:12px;background:white;padding:20px;border-radius:12px;max-width:600px;width:100%;max-height:90dvh;overflow:auto;overflow-wrap:anywhere}.detail-panel img{max-width:100%;height:auto}
</style>
