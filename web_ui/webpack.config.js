const path = require('path');

module.exports = {
  entry: './src/nvl-bundle.js',
  output: {
    path: path.resolve(__dirname, 'static/js/dist'),
    filename: 'nvl.bundle.js',
    library: 'NVL',
    libraryTarget: 'window',
    clean: true
  },
  mode: 'production',
  resolve: {
    extensions: ['.js', '.json']
  },
  optimization: {
    minimize: true
  }
};
