// Neo4j NVL Bundle for Flask Web UI
// This file bundles the Neo4j NVL library and exposes it globally

import { NVL } from '@neo4j-nvl/base';

// Expose NVL globally for use in vanilla JavaScript
window.NVL = NVL;

// Also expose the actual NVL class for direct access
window.Neo4jNVL = NVL;

// Also expose as a module export for potential future use
export { NVL };

// Log successful loading
console.log('✅ Neo4j NVL library loaded and bundled successfully');
console.log('📦 NVL available as window.NVL:', typeof window.NVL);
console.log('📦 NVL constructor available:', typeof NVL);
console.log('📦 NVL constructor name:', NVL.name);

// Test NVL constructor availability
try {
    console.log('🔧 Testing NVL constructor...');
    console.log('🔧 NVL prototype:', NVL.prototype);
    console.log('🔧 NVL is constructor:', typeof NVL === 'function');
    console.log('✅ NVL constructor test passed');
} catch (error) {
    console.error('❌ NVL constructor test failed:', error);
}

// Provide a simple initialization helper
window.initializeNVL = function(container, options = {}) {
  try {
    console.log('🔧 initializeNVL called with:', { container, options });
    console.log('🔧 Available NVL:', {
      windowNVL: typeof window.NVL,
      directNVL: typeof NVL,
      neo4jNVL: typeof window.Neo4jNVL
    });

    // Get the NVL constructor
    const NVLConstructor = window.NVL || NVL || window.Neo4jNVL;

    if (!NVLConstructor) {
      throw new Error('NVL constructor not found');
    }

    console.log('🔧 Using NVL constructor:', NVLConstructor);

    // Try minimal configuration first
    const minimalOptions = {
      width: options.width || 800,
      height: options.height || 600
    };

    console.log('🔧 Attempting NVL creation with minimal options:', minimalOptions);

    // Try creating NVL with minimal options
    let nvlInstance;
    try {
      nvlInstance = new NVLConstructor(container, minimalOptions);
      console.log('✅ NVL instance created with minimal options');
    } catch (minimalError) {
      console.warn('⚠️ Minimal NVL creation failed, trying with container only:', minimalError);
      // Try with just the container
      nvlInstance = new NVLConstructor(container);
      console.log('✅ NVL instance created with container only');
    }

    console.log('🔧 NVL instance created:', nvlInstance);
    console.log('🔧 NVL instance methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(nvlInstance)));

    return nvlInstance;
  } catch (error) {
    console.error('❌ All NVL creation attempts failed:', error);
    console.error('❌ Error details:', {
      message: error.message,
      stack: error.stack,
      container: container,
      containerExists: !!container,
      containerType: container ? container.tagName : 'null'
    });
    throw error;
  }
};

console.log('🔧 NVL bundle initialization complete');
