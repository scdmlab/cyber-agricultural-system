export const basemaps = [
  { 
    id: 'osm', 
    name: 'OpenStreetMap', 
    thumbnail: '/thumbnails/osm.png', 
    url: 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'
  },
  { 
    id: 'satellite', 
    name: 'Satellite', 
    thumbnail: '/thumbnails/satellite.png', 
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  },
  {
    id: 'esri_worldterrain',
    name: 'Esri WorldTerrain',
    thumbnail: '/thumbnails/esri_worldterrain.png',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: USGS, Esri, TANA, DeLorme, and NPS',
    maxZoom: 13
  },
  {
    id: 'esri_worldshadedrelief',
    name: 'Esri WorldShadedRelief',
    thumbnail: '/thumbnails/esri_worldshadedrelief.png',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri',
    maxZoom: 13
  },
  {
    id: 'esri_natgeoworldmap',
    name: 'Esri NatGeoWorldMap',
    thumbnail: '/thumbnails/esri_natgeoworldmap.png',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',
    maxZoom: 16
  },
  {
    id: 'usgs_ustopo',
    name: 'USGS USTopo',
    thumbnail: '/thumbnails/usgs_ustopo.png',
    url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
    maxZoom: 20,
    attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
  }
];

export function getBasemapUrl(id) {
  const basemap = basemaps.find(b => b.id === id);
  return basemap ? basemap.url : basemaps[0].url;
}