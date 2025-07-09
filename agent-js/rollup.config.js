import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import terser from '@rollup/plugin-terser';

export default [
  // ESM build
  {
    input: 'src/index.js',
    output: {
      file: 'dist/simple-agent.esm.js',
      format: 'es'
    },
    plugins: [
      resolve({ browser: true }),
      commonjs()
    ],
    external: ['idb', 'uuid', 'date-fns']
  },
  // UMD build
  {
    input: 'src/index.js',
    output: {
      file: 'dist/simple-agent.umd.js',
      format: 'umd',
      name: 'SimpleAgent',
      globals: {
        'idb': 'idb',
        'uuid': 'uuid',
        'date-fns': 'dateFns'
      }
    },
    plugins: [
      resolve({ browser: true }),
      commonjs(),
      terser()
    ],
    external: ['idb', 'uuid', 'date-fns']
  }
]; 