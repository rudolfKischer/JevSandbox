import './tips.js';
import { mountShell } from './shell.js';

const PAGES = {
  'index.html': { module: './app.js', title: 'Alignment' },
  'pron.html': { module: './pron.js', title: 'Pronunciation' },
  'sources.html': { module: './sources.js', title: 'Source comparison' },
  'regions.html': { module: './regions.js', title: 'Regional pronunciation' },
};

const instances = new Map();
const readying = new Map();
const views = new Map();
let current = null;
let token = 0;

const main = () => document.getElementById('main');
const idle = () => new Promise(resolve => (window.requestIdleCallback ? requestIdleCallback(resolve, { timeout: 400 }) : setTimeout(resolve, 60)));

const fileOf = path => {
  const name = path.split('/').pop();
  return PAGES[name] ? name : 'index.html';
};

async function view(file) {
  if (!views.has(file)) views.set(file, fetch(`views/${file.replace('.html', '')}.html`).then(reply => reply.text()));
  return views.get(file);
}

function ready(file) {
  if (!readying.has(file)) {
    readying.set(file, Promise.all([import(PAGES[file].module), view(file)]).then(async ([module, html]) => {
      await module.load();
      const node = document.createElement('div');
      node.className = 'page-root';
      node.innerHTML = html;
      instances.set(file, { file, module, node, built: false });
      return instances.get(file);
    }));
  }
  return readying.get(file);
}

function attach(instance, options) {
  main().replaceChildren(instance.node);
  if (!instance.built) {
    instance.module.mount(options);
    instance.built = true;
  }
}

async function show(file) {
  const mine = ++token;
  const instance = await ready(file);
  if (mine !== token) return;
  if (current) current.module.deactivate();
  attach(instance, {});
  current = instance;
  document.title = PAGES[file].title;
  instance.module.activate();
  window.scrollTo(0, 0);
}

async function preload() {
  for (const file of Object.keys(PAGES)) {
    const instance = await ready(file);
    if (!instance.built && current) {
      const keep = current;
      attach(instance, { preload: true });
      main().replaceChildren(keep.node);
      keep.module.activate();
    }
    await idle();
  }
}

function internal(link) {
  const url = new URL(link.href, location.href);
  return url.origin === location.origin && PAGES[url.pathname.split('/').pop()] ? url : null;
}

document.addEventListener('click', event => {
  const link = event.target.closest('a[href]');
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
  const url = internal(link);
  if (!url) return;
  event.preventDefault();
  if (url.pathname === location.pathname && !url.search && !location.search) return;
  history.pushState({}, '', url.pathname + url.search);
  show(fileOf(url.pathname));
});

window.addEventListener('popstate', () => show(fileOf(location.pathname)));

mountShell({});
show(fileOf(location.pathname)).then(preload);
