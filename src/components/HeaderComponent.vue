<template>
  <header class="bg-green-600 text-black font-sans flex justify-between items-center w-full h-12 px-0">
    <div class="bg-gray-700 text-white px-4 py-2 flex items-center">
      <h1 class="text-2xl font-bold m-0">Crop Yield Prediction</h1>
    </div>
    <nav class="flex items-center">
      <a href="#" @click.prevent="showReferences" class="text-black no-underline mx-4 hover:underline hover:text-gray-700 flex items-center">
        <Icon icon="mdi:file-document" :width="24" :height="24" :inline="true" class="mr-1" />
        References
      </a>
      <a href="#" @click.prevent="showResearchGroup" class="text-black no-underline mx-4 hover:underline hover:text-gray-700 flex items-center">
        <Icon icon="mdi:account-group" :width="24" :height="24" :inline="true" class="mr-1" />
        Research Group
      </a>
      <a href="https://github.com/scdmlab/" target="_blank" class="text-black no-underline mx-4 hover:underline hover:text-gray-700 flex items-center"> 
        <Icon icon="mdi:github" :width="24" :height="24" :inline="true" class="mr-1" />
        Github
      </a>
    </nav>

    <PopupWindow v-if="showReferencesPopup" @close="showReferencesPopup = false" title="References" width="600px" height="400px">
      <div v-html="referencesContent"></div>
    </PopupWindow>

    <PopupWindow v-if="showResearchGroupPopup" @close="showResearchGroupPopup = false" title="Research Group" width="500px" height="400px">
      <div v-html="researchGroupContent"></div>
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
        <p>References:</p>
        <p>Corn yield prediction and uncertainty analysis based on remotely sensed variables using a Bayesian neural network approach(href).</p>
        <p>In this project, we have developed models and tools to provide near real-time in-season crop yield predictions for two mainly commodity crops (i.e., corn and soybeans) at the county-level for the CONUS, based on state-of-the-art remote sensing and deep learning technologies.</p>
        <p>The predicted yield information will be disseminated through a web-based cyber-platform for free public use, which is critical for a variety of stakeholders, such as for US producers to make operational decisions; for insurance companies to help with claim and compliance assessment; for agricultural finance companies to support businesses of distribution, processing, and marketing.</p>
        <p>The predicted yield information will also be delivered to USDA for decision support to maintain the stability of the food supply and price, to reduce food security threats. The proposed tool could potentially reduce the USDA NASS survey response burden and cost, improve the efficiency and data quality, and enhance USDA NASS crop yield prediction capability.</p>
        <p>Therefore, the proposed project will add value to NASS's existing crop yield estimation program and have broad impacts on many stakeholders.</p>
      `,
      researchGroupContent: `
        <ul>
          <li>Zhou Zhang, UW-Madison, zzhang347@wisc.edu</li>
          <li>Yuchi Ma, UW-Madison, ma286@wisc.edu</li>
          <li>Zeyu Cao, UW-Madison, zcao96@wisc.edu</li>
          <li>Zhengwei Yang, REE-NASS, zhengwei.yang@usda.gov</li>
          <li>Qunying Huang, UW-Madison, qhuang46@wisc.edu</li>
          <li>Meiliu Wu, UW-Madison, mwu233@wisc.edu</li>
          <li>Songxi Yang, UW-Madison, songxi.yang@wisc.edu</li>
          <li>Haiyue Liu, UW-Madison, hliu746@wisc.edu</li>
        </ul>
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

