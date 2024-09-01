<!-- HeaderComponent.vue -->
<template>
  <header>
    <div class="title-container">
      <h1>Crop Yield Prediction</h1>
    </div>
    <nav>
      <a href="#">
        <span class="iconify" data-icon="mdi:paper"></span>
        References
      </a>
      <a href="#">
        <span class="iconify" data-icon="mdi:account-group"></span>
        Research Group
      </a>
      <a href="#">
        <span class="iconify" data-icon="mdi:github"></span>
        Github
      </a>
    </nav>
  </header>
</template>

<script>
import  {Icon}  from '@iconify/vue'

export default {
  name: 'HeaderComponent',
  components: {
    Icon
  }
}
</script>

<style scoped>
header {
  background-color: var(--color-background-soft);
  color: #000;
  font-family: 'Arial', sans-serif;
  padding: var(--space-medium) var(--space-large);
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  padding: 0;
  height: 46px;
}

.title-container {
  background-color: var(--color-background-soft); /* New background color for the title container */
  padding: var(--space-small) var(--space-medium);; /* Slightly right to the text */
  display: flex;
  align-items: center;
}

h1 {
  margin: 0;
  font-size: 24px;
}

nav a {
  color: var(--color-text);
  text-decoration: none;
  margin-left: var(--space-large);
  margin-right: var(--space-medium);
}

nav a:hover {
  text-decoration: underline;
  color: var(--color-text-hover);
}
</style>
