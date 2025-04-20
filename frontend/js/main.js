import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let scene, camera, renderer, controls;
init();
createInstancedSpheres(25);
animate();

function init() {
  // -- Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  document.getElementById('container').appendChild(renderer.domElement);

  // -- Scene & Camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
  camera.position.set(0, 0, 25);

  // -- Lights
  scene.add(new THREE.HemisphereLight(0x404050, 0x202030, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 1);
  key.position.set(5,10,5);
  scene.add(key);

  // -- Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // -- Handle Resize
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
}

function createInstancedSpheres(count) {
  // High‑poly sphere geometry
  const geo = new THREE.SphereGeometry(1, 64, 64);

  // Glossy white material
  const mat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    metalness: 0.2,
    roughness: 0.1,
    clearcoat: 1,
    clearcoatRoughness: 0.03
  });

  // Instanced mesh
  const inst = new THREE.InstancedMesh(geo, mat, count);
  const dummy = new THREE.Object3D();

  for (let i = 0; i < count; i++) {
    // random position in a shell radius 8–18
    const phi   = Math.acos(2*Math.random() - 1);
    const theta = 2*Math.PI*Math.random();
    const r     = THREE.MathUtils.randFloat(8, 18);
    dummy.position.set(
      r * Math.sin(phi)*Math.cos(theta),
      r * Math.sin(phi)*Math.sin(theta),
      r * Math.cos(phi)
    );

    // random rotation & scale
    dummy.rotation.set(
      Math.random()*Math.PI,
      Math.random()*Math.PI,
      Math.random()*Math.PI
    );
    const s = THREE.MathUtils.randFloat(0.5, 1.2);
    dummy.scale.set(s, s, s);

    dummy.updateMatrix();
    inst.setMatrixAt(i, dummy.matrix);
  }

  scene.add(inst);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
