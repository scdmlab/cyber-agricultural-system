<!-- HeaderComponent.vue -->
<template>
  <header>
    <h1>GIS Data Visualization</h1>
    <nav>
      <a href="#">Home</a>
      <a href="#">About</a>
      <a href="#">Contact</a>
    </nav>
  </header>
</template>

<script>
export default {
  name: 'HeaderComponent'
}
</script>

<style scoped>
header {
  background-color: var(--color-background-soft);
  color: var(--color-text);
  padding: var(--space-medium) var(--space-large);
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

h1 {
  margin: 0;
  font-size: var(--font-size-large);
}

nav a {
  color: var(--color-text);
  text-decoration: none;
  margin-left: var(--space-large);
}

nav a:hover {
  text-decoration: underline;
  color: var(--color-text-hover);
}
</style>
