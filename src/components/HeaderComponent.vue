<template>
  <header>
    <div class="title-container">
      <h1>Crop Yield Prediction</h1>
    </div>
    <nav>
      <a href="#" @click.prevent="showReferences">
        <Icon icon="mdi:file-document" :width="24" :height="24" :inline="true" />
        References
      </a>
      <a href="#" @click.prevent="showResearchGroup">
        <Icon icon="mdi:account-group" :width="24" :height="24" :inline="true" />
        Research Group
      </a>
      <a href="https://github.com/scdmlab/" target="_blank"> 
        <Icon icon="mdi:github" :width="24" :height="24" :inline="true" />
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

<style scoped>
header {
  background-color: #04AA6D; /* Changed to green */
  color: #000;
  font-family: 'Arial', sans-serif;
  padding: var(--space-medium) var(--space-large);
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  padding: 0;
  height: 50px;
}

.title-container {
  background-color: rgb(85, 85, 85); /* Changed to gray */
  color: white; /* Text color changed to white */
  padding: var(--space-small) var(--space-medium);
  display: flex;
  align-items: center;
}

h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold; /* Made the title bolder */
}

nav a {
  color: black;
  text-decoration: none;
  margin-left: var(--space-large);
  margin-right: var(--space-medium);
}

nav a:hover {
  text-decoration: underline;
  color: var(--color-text-hover);
}
</style>