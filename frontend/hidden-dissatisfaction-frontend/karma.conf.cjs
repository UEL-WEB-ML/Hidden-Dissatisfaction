module.exports = (config) => {
  config.set({
    browsers: ['jsdom'],
    frameworks: ['jasmine'],
    plugins: ['karma-jasmine', 'karma-jsdom-launcher', '@angular-devkit/build-angular/plugins/karma'],
  });
};
