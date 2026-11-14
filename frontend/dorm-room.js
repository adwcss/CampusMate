"use strict";
window.DormRoom = (() => {
  const stage = document.querySelector("#dorm-room-stage");
  const plan = document.querySelector("#dorm-room-plan");
  const mode = document.querySelector("#dorm-room-mode");
  const caption = document.querySelector("#dorm-room-caption");
  const controls = [...document.querySelectorAll("[data-dorm-camera]")];
  const T = window.THREE;
  let renderer, scene, camera, anchors, pick, bedMeshes;
  let width, depth, angle, pitch, scale, flat, drag;
  const ray = new T.Raycaster();
  const point = new T.Vector2();

  function box(parent, color, x, y, z, w, h, d) {
    const mesh = new T.Mesh(new T.BoxGeometry(w, h, d), new T.MeshStandardMaterial({color, roughness: .82}));
    mesh.position.set(x, y, z);
    parent.add(mesh);
    return mesh;
  }

  function loft(bed, x, z, palette) {
    const {frame, wood, panel, cloth} = palette;
    const side = Math.sign(x);
    const group = new T.Group();
    group.position.set(x, 0, z);
    scene.add(group);
    const add = (...args) => box(group, ...args);
    const deck = add(frame, 0, 1.78, 0, 1.09, .14, 1.98);
    const mattress = add(0xf4efe4, 0, 1.91, 0, .94, .15, 1.83);
    const blanket = add(cloth, 0, 2.01, .27, .93, .07, 1.14);
    const pillow = add(0xeee8db, 0, 2.03, -.66, .63, .14, .32);
    const rail = add(panel, -side * .53, 2.04, -.20, .045, .30, 1.44);
    for (const mesh of [deck, mattress, blanket, pillow, rail]) {
      mesh.userData.bed = bed;
      bedMeshes.push(mesh);
    }
    for (const dx of [-.49, .49]) for (const dz of [-.92, .92]) {
      add(frame, dx, .99, dz, .055, 1.98, .055);
    }
    add(wood, side * .16, .78, -.11, .77, .08, 1.47);
    add(panel, side * .44, 1.34, -.16, .23, .06, 1.28);
    add(panel, 0, .74, -.74, .90, 1.48, .36);
    add(frame, -side * .46, .80, -.74, .024, .25, .06);
    for (const dz of [.57, .88]) add(frame, -side * .59, .96, dz, .045, 1.92, .045);
    for (let step = 1; step <= 5; step++) add(frame, -side * .59, step * .30, .725, .075, .035, .33);
    const chair = -side * .62;
    add(panel, chair, .46, -.15, .34, .07, .39);
    add(panel, chair - side * .15, .68, -.15, .05, .38, .35);
    for (const dx of [-.12, .12]) for (const dz of [-.14, .14]) {
      add(frame, chair + dx, .21, -.15 + dz, .026, .42, .026);
    }
    if (palette.curtains) {
      for (let fold = 0; fold < 6; fold++) {
        add(0x968578, side * (.48 + (fold % 2) * .025), 2.15, -.86 + fold * .13, .045, .40, .13);
      }
    }
    const label = document.createElement("button");
    label.type = "button";
    label.className = "dorm-room-marker";
    label.textContent = bed.id;
    label.setAttribute("aria-label", `查看${bed.name}详情`);
    label.onclick = () => pick(bed);
    stage.append(label);
    anchors.push({label, position: new T.Vector3(x, 2.47, z)});
  }

  function draw() {
    if (!renderer || flat || !stage.clientWidth) return;
    const w = stage.clientWidth, h = stage.clientHeight;
    if (renderer.domElement.style.width !== `${w}px` || renderer.domElement.style.height !== `${h}px`) renderer.setSize(w, h);
    const aspect = w / h;
    const span = Math.max(depth * .67, depth * .56 / aspect) / scale;
    camera.left = -span * aspect;
    camera.right = span * aspect;
    camera.top = span;
    camera.bottom = -span;
    camera.position.set(15 * Math.cos(pitch) * Math.sin(angle), 15 * Math.sin(pitch), 15 * Math.cos(pitch) * Math.cos(angle));
    camera.lookAt(0, .72, 0);
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
    for (const {label, position} of anchors) {
      const {x, y} = position.clone().project(camera);
      label.hidden = Math.abs(x) > .98 || Math.abs(y) > .98;
      label.style.left = `${(x + 1) * 50}%`;
      label.style.top = `${(1 - y) * 50}%`;
    }
    controls.find(control => control.dataset.dormCamera === "top").setAttribute("aria-pressed", String(pitch > 1.5));
  }

  function setFlat(value) {
    flat = value;
    stage.hidden = value;
    plan.hidden = !value;
    controls.forEach(control => { control.disabled = value; });
    mode.textContent = value ? "返回 3D" : "查看平面图";
    mode.setAttribute("aria-pressed", String(value));
    draw();
  }

  function reset() {
    angle = .47;
    pitch = .91;
    scale = 1;
  }

  function washArea(four, back) {
    const z = back + .65;
    const chrome = 0x9ca5a5;
    box(scene, 0xb0b3af, 0, .03, z, 3.55, .07, 1.22);
    box(scene, four ? 0xdedbd3 : 0x514d48, -.93, .78, z, 1.38, .16, .55);
    box(scene, four ? 0xaaa69d : 0x383a39, -.93, 1.37, z - .30, 1.37, .49, .065);
    box(scene, 0xb9ced1, -.93, 1.37, z - .255, 1.29, .41, .03);
    const basinMaterial = new T.MeshStandardMaterial({color: 0xf9f7ee, roughness: .27});
    for (const x of [-1.28, -.58]) {
      const rim = new T.Mesh(new T.TorusGeometry(.19, .025, 10, 28), basinMaterial);
      rim.rotation.x = -Math.PI / 2;
      rim.scale.set(1.17, .82, 1);
      rim.position.set(x, .87, z + .035);
      scene.add(rim);
      box(scene, chrome, x, .94, z - .17, .045, .18, .045);
      box(scene, chrome, x, 1.02, z - .11, .04, .035, .13);
    }
    box(scene, 0x8c9794, 1.13, .09, z, .92, .07, 1.04);
    const screen = box(scene, 0x9ebfba, .64, .70, z - .07, .04, 1.2, .9);
    screen.material.transparent = true;
    screen.material.opacity = .50;
    screen.material.depthWrite = false;
    box(scene, 0x454b49, .64, .71, z - .52, .045, 1.21, .04);
    box(scene, chrome, 1.31, 1.04, z - .45, .035, 1.66, .035);
    box(scene, chrome, 1.31, 1.86, z - .30, .04, .04, .31);
    box(scene, chrome, 1.31, 1.83, z - .18, .22, .04, .19);
    if (four) {
      box(scene, 0xf2f0e8, .17, .47, z - .30, .31, .4, .16);
      const seat = new T.Mesh(new T.SphereGeometry(.20, 20, 12), basinMaterial);
      seat.scale.set(.87, .62, 1.17);
      seat.position.set(.17, .25, z - .07);
      scene.add(seat);
    }
  }

  function init() {
    renderer = new T.WebGLRenderer({antialias: true, alpha: true});
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.outputColorSpace = T.SRGBColorSpace;
    const canvas = renderer.domElement;
    canvas.setAttribute("aria-hidden", "true");
    stage.append(canvas);
    camera = new T.OrthographicCamera(-1, 1, 1, -1, .1, 50);
    new ResizeObserver(draw).observe(stage);
    canvas.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      drag = {id: event.pointerId, x: event.clientX, y: event.clientY, angle, pitch};
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener("pointermove", event => {
      if (drag?.id !== event.pointerId) return;
      angle = drag.angle - (event.clientX - drag.x) * .011;
      pitch = Math.max(.27, Math.min(1.56, drag.pitch + (event.clientY - drag.y) * .009));
      draw();
    });
    canvas.addEventListener("pointerup", event => {
      if (drag?.id !== event.pointerId) return;
      const click = Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 5;
      drag = null;
      if (!click) return;
      const bounds = canvas.getBoundingClientRect();
      point.set((event.clientX - bounds.left) / bounds.width * 2 - 1, 1 - (event.clientY - bounds.top) / bounds.height * 2);
      ray.setFromCamera(point, camera);
      const hit = ray.intersectObjects(bedMeshes, false)[0];
      if (hit) pick(hit.object.userData.bed);
    });
    canvas.addEventListener("pointercancel", () => { drag = null; });
    canvas.addEventListener("wheel", event => {
      if (!event.ctrlKey) return;
      event.preventDefault();
      scale = Math.max(.76, Math.min(1.8, scale * Math.exp(-event.deltaY * .004)));
      draw();
    }, {passive: false});
    mode.onclick = () => setFlat(!flat);
    for (const control of controls) control.onclick = () => {
      const action = control.dataset.dormCamera;
      if (action === "left") angle -= Math.PI / 8;
      if (action === "right") angle += Math.PI / 8;
      if (action === "top") pitch = pitch > 1.5 ? .91 : 1.56;
      if (action === "in") scale = Math.min(1.8, scale * 1.15);
      if (action === "out") scale = Math.max(.76, scale / 1.15);
      if (action === "reset") reset();
      draw();
    };
  }

  function show(roomType, beds, onPick) {
    try {
      if (!renderer) init();
    } catch {
      mode.disabled = true;
      setFlat(true);
      caption.textContent = "此浏览器无法显示 3D，可继续使用平面图和床号列表。";
      return;
    }
    if (scene) scene.traverse(item => {
      item.geometry?.dispose();
      item.material?.dispose();
    });
    anchors?.forEach(({label}) => label.remove());
    anchors = [];
    bedMeshes = [];
    pick = onPick;
    const four = roomType === "siren";
    const palette = four ? {frame: 0xe6ddc6, wood: 0xbfae92, panel: 0x758295, cloth: 0xd4cec0}
      : {frame: 0x43474a, wood: 0xb88c62, panel: 0x8b7662, cloth: 0xd0baa1, curtains: true};
    width = 3.7;
    depth = four ? 7.05 : 8.65;
    scene = new T.Scene();
    scene.add(new T.HemisphereLight(0xfff6e5, 0x999ba7, 1.05));
    const sun = new T.DirectionalLight(0xfff0d6, .92);
    sun.position.set(-3, 8, 2);
    scene.add(sun);
    box(scene, 0xc2b3a0, 0, -.16, 0, width + .24, .28, depth + .22);
    const tileDepth = depth / 11;
    for (let row = 0; row < 11; row++) for (let column = 0; column < 6; column++) {
      box(scene, (row + column) % 3 ? 0xe1d6c3 : 0xd9cdbb, (column - 2.5) * width / 6, 0,
          (row - 5) * tileDepth, width / 6 - .013, .045, tileDepth - .013);
    }
    const back = -depth / 2;
    box(scene, 0xf0e6d4, 0, .48, back, width, .96, .12);
    box(scene, 0x64605c, 0, 1.58, back, 1.55, 1.38, .13);
    for (const x of [-.37, .37]) box(scene, 0xb9d9e4, x, 1.59, back + .07, .68, 1.2, .04);
    for (const side of [-1, 1]) {
      box(scene, 0xe9dfce, side * 1.32, 1.38, back, 1.04, 2.75, .12);
      box(scene, 0xe9dfce, side * width / 2, .32, 0, .12, .64, depth);
      box(scene, 0xe9dfce, side * 1.29, .32, depth / 2, 1.15, .64, .12);
    }
    box(scene, 0x8d7763, .62, .64, depth / 2 - .38, .06, 1.26, .72);
    washArea(four, back);
    beds.forEach(bed => {
      const x = bed.x < 50 ? -1.20 : 1.20;
      const z = bed.y < 55 ? (four ? -1.19 : -1.96) : bed.y > 75 ? (four ? 1.10 : 2.16) : .10;
      loft(bed, x, z, palette);
    });
    reset();
    setFlat(false);
    caption.textContent = "床架、桌柜和卫浴材质参考宿舍总览实拍，床号和相对位置沿用原平面图。卫浴细节为示意，实际配置以学校安排为准。";
  }
  return {show};
})();
