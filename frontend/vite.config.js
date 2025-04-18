
export default {
  build: {
    outDir: '../static',
    emptyOutDir: true
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8080'
    }
  }
};
