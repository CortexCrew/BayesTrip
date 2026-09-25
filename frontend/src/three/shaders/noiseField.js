/* Animated noise-field background shader — vertex + fragment */

export const noiseFieldVertex = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

export const noiseFieldFragment = /* glsl */ `
  uniform float uTime;
  uniform vec2  uResolution;
  uniform vec3  uColor1;
  uniform vec3  uColor2;
  varying vec2  vUv;

  /* Simplex-like hash */
  vec3 hash33(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract(vec3(p.x * p.y, p.y * p.z, p.z * p.x));
  }

  float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float n = mix(
      mix(mix(dot(hash33(i), f), dot(hash33(i + vec3(1,0,0)), f - vec3(1,0,0)), f.x),
          mix(dot(hash33(i + vec3(0,1,0)), f - vec3(0,1,0)), dot(hash33(i + vec3(1,1,0)), f - vec3(1,1,0)), f.x), f.y),
      mix(mix(dot(hash33(i + vec3(0,0,1)), f - vec3(0,0,1)), dot(hash33(i + vec3(1,0,1)), f - vec3(1,0,1)), f.x),
          mix(dot(hash33(i + vec3(0,1,1)), f - vec3(0,1,1)), dot(hash33(i + vec3(1,1,1)), f - vec3(1,1,1)), f.x), f.y),
      f.z
    );
    return n * 0.5 + 0.5;
  }

  float fbm(vec3 p) {
    float value = 0.0;
    float amp   = 0.5;
    for (int i = 0; i < 4; i++) {
      value += amp * noise(p);
      p *= 2.0;
      amp *= 0.5;
    }
    return value;
  }

  void main() {
    vec2 uv = vUv;
    float n = fbm(vec3(uv * 3.0, uTime * 0.1));
    vec3 color = mix(uColor1, uColor2, n);
    color *= 0.15; /* keep it very subtle */
    float vignette = 1.0 - length(uv - 0.5) * 1.0;
    color *= smoothstep(0.0, 0.7, vignette);
    gl_FragColor = vec4(color, 1.0);
  }
`
