/* Fresnel edge-glow shader material — makes 3D objects glow on silhouette edges */

export const fresnelVertex = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vNormal  = normalize(normalMatrix * normal);
    vViewDir = normalize(cameraPosition - worldPos.xyz);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`

export const fresnelFragment = /* glsl */ `
  uniform vec3  uColor;
  uniform float uIntensity;
  uniform float uPower;
  varying vec3  vNormal;
  varying vec3  vViewDir;

  void main() {
    float fresnel = pow(1.0 - max(dot(vNormal, vViewDir), 0.0), uPower);
    vec3 color = uColor * fresnel * uIntensity;
    gl_FragColor = vec4(color, fresnel * 0.8);
  }
`
