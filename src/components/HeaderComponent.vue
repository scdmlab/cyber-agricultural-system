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
  background-color: #333;
  color: white;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
box-sizing: border-box;
}

h1 {
  margin: 0;
  font-size: 1.5em;
}

nav a {
  color: white;
  text-decoration: none;
  margin-left: 20px;
}

nav a:hover {
  text-decoration: underline;
}
</style>