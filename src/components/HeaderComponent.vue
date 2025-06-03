<template>
  <header class="bg-gradient-to-r from-green-600 via-green-700 to-green-800 text-white font-sans shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex flex-row justify-between items-center gap-2">
      <div class="flex items-center">
        <div class="flex items-center">
          <Icon icon="mdi:sprout" class="text-green-200 mr-2" :width="24" :height="24" :inline="true" />
          <h1 class="text-lg sm:text-xl md:text-2xl font-bold tracking-tight">Crop Yield Prediction</h1>
        </div>
      </div>
      <nav class="flex flex-wrap justify-end items-center gap-3 sm:gap-4">
        <a href="#" @click.prevent="showReferences" class="header-link text-sm sm:text-base">
          <Icon icon="mdi:file-document" :width="20" :height="20" :inline="true" class="mr-1" />
          Project Intro
        </a>
        <a href="#" @click.prevent="showResearchGroup" class="header-link text-sm sm:text-base">
          <Icon icon="mdi:account-group" :width="20" :height="20" :inline="true" class="mr-1" />
          Research Group
        </a>
        <a href="https://github.com/scdmlab/cyber-agricultural-system/" target="_blank" class="header-link text-sm sm:text-base">
          <Icon icon="mdi:github" :width="20" :height="20" :inline="true" class="mr-1" />
          Github
        </a>
      </nav>
    </div>

    <PopupWindow 
      v-if="showReferencesPopup" 
      @close="showReferencesPopup = false" 
      title="Project Intro" 
      :initial-width="600" 
      :initial-height="400"
      :min-width="400"
      :max-width="800"
      :min-height="300"
      :max-height="600"
    >
      <div class="prose prose-sm md:prose max-w-none text-gray-800 p-4" v-html="referencesContent"></div>
    </PopupWindow>

    <PopupWindow 
      v-if="showResearchGroupPopup" 
      @close="showResearchGroupPopup = false" 
      title="Research Group" 
      :initial-width="800" 
      :initial-height="600"
      :min-width="400"
      :max-width="1200"
      :min-height="300"
      :max-height="600"
    >
      <div class="prose prose-sm md:prose max-w-none text-gray-800 p-4" v-html="researchGroupContent"></div>
    </PopupWindow>
  </header>
</template>

<script>
import { Icon } from '@iconify/vue'
import PopupWindow from './PopupWindow.vue'

export default {
  name: 'HeaderComponent',
  components: {
    Icon,
    PopupWindow
  },
  data() {
    return {
      showReferencesPopup: false,
      showResearchGroupPopup: false,
      referencesContent: `
        <div class="space-y-6">
          <p>This web tool provides bi-weekly county-level crop yield prediction and uncertainty for two main commodity crops (corn and soybean), using satellite images and Bayesian neural network.</p>
          
          <p>The detailed method is provided in our published work "Corn yield prediction and uncertainty analysis based on remotely sensed variables using a Bayesian neural network approach" [Ma et el., 2021].</p>
          
          <p>This is a collaborative work between UW-Madison and USDA NASS, and it adds value to NASS's existing state-level crop yield estimation program.</p>
          
          <p>This project is funded by USDA NIFA Agriculture and Food Research Initiative Project (Award # 2022-67021-36468).</p>
        </div>
      `,
      researchGroupContent: `
        <div class="space-y-6">
          <div>
            <p class="font-bold text-lg mb-2">PI:</p>
            <p class="ml-4">Zhou Zhang, UW-Madison, zzhang347@wisc.edu</p>
          </div>
          
          <div>
            <p class="font-bold text-lg mb-2">Co-PIs:</p>
            <div class="ml-4 space-y-1">
              <p>Qunying Huang, UW-Madison, qhuang46@wisc.edu</p>
              <p>Zhengwei Yang, USDA NASS, zhengwei.yang@usda.gov</p>
            </div>
          </div>

          <div>
            <p class="font-bold text-lg mb-2">Students:</p>
            <div class="ml-4 space-y-1">
              <p>Yuchi Ma, UW-Madison</p>
              <p>Xiaoyu Wang, UW-Madison</p>
              <p>Meiliu Wu, UW-Madison</p>
              <p>Songxi Yang, UW-Madison</p>
              <p>Haiyue Liu, UW-Madison</p>
            </div>
          </div>
        </div>
      `
    }
  },
  methods: {
    showReferences() {
      this.showReferencesPopup = true
    },
    showResearchGroup() {
      this.showResearchGroupPopup = true
    }
  }
}
</script>

<style scoped>
.header-link {
  @apply flex items-center text-white hover:text-green-100 transition-all duration-200 ease-in-out px-2 py-1 rounded-md hover:bg-green-600/30 font-medium;
}

/* Add animation for hover effect */
@keyframes pulse-light {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}

.header-link:hover .mr-2 {
  @apply text-green-200;
  animation: pulse-light 2s ease-in-out infinite;
}
</style>