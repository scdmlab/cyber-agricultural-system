<!-- App.vue -->
<template>
  <div id="app">
    <HeaderComponent />
    <MapComponent />
  </div>
</template>

<script>
import HeaderComponent from './components/HeaderComponent.vue'
import MapComponent from './components/MapComponent.vue'

export default {
  name: 'App',
  components: {
    HeaderComponent,
    MapComponent
  }
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  padding: 0;
}
</style>