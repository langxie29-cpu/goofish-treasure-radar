<script setup lang="ts">
import { RouterView } from 'vue-router'
import MobileStatus from '@/components/MobileStatus.vue'
import Toaster from '@/components/ui/toast/Toaster.vue'
</script>

<template>
  <MobileStatus v-if="$route.path !== '/backend'" />
  <RouterView />
  <Toaster />
</template>
