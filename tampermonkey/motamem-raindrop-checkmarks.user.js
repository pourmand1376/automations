// ==UserScript==
// @name         Motamem Raindrop Checkmarks
// @namespace    https://github.com/pourmand1376/automations
// @version      1.0.0
// @description  Marks Motamem links that are present in the Raindrop URL list.
// @match        https://motamem.org/*
// @match        http://motamem.org/*
// @grant        GM_xmlhttpRequest
// @connect      github.com
// @connect      raw.githubusercontent.com
// ==/UserScript==

(function () {
  "use strict";

  const LIST_URL = "https://github.com/pourmand1376/automations/raw/refs/heads/main/state/motamem_urls.json";
  const CACHE_KEY = "motamem-raindrop-url-list-v1";
  const CACHE_TTL_MS = 4 * 60 * 60 * 1000;
  const MARKER_ATTRIBUTE = "data-motamem-raindrop-checkmark";

  function normalizeUrl(value) {
    try {
      const url = new URL(value, window.location.href);
      url.hash = "";
      return url.href.replace(/\/$/, "");
    } catch {
      return null;
    }
  }

  function readCache() {
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (cached && Date.now() - cached.savedAt < CACHE_TTL_MS && Array.isArray(cached.urls)) {
        return new Set(cached.urls.map(normalizeUrl).filter(Boolean));
      }
    } catch (error) {
      console.warn("Motamem checkmarks: could not read cache", error);
    }
    return null;
  }

  function requestList() {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "GET",
        url: LIST_URL,
        onload(response) {
          if (response.status < 200 || response.status >= 300) {
            reject(new Error(`HTTP ${response.status}`));
            return;
          }
          try {
            const urls = JSON.parse(response.responseText);
            if (!Array.isArray(urls)) throw new Error("Expected a JSON array");
            const normalized = urls.map(normalizeUrl).filter(Boolean);
            localStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), urls: normalized }));
            resolve(new Set(normalized));
          } catch (error) {
            reject(error);
          }
        },
        onerror() {
          reject(new Error("Could not download the URL list"));
        },
      });
    });
  }

  function addCheckmarks(urls) {
    document.querySelectorAll("a[href]").forEach((link) => {
      if (link.hasAttribute(MARKER_ATTRIBUTE)) return;
      if (!urls.has(normalizeUrl(link.href))) return;

      const marker = document.createElement("span");
      marker.textContent = " ✓";
      marker.title = "Saved in Raindrop";
      marker.setAttribute(MARKER_ATTRIBUTE, "true");
      marker.style.cssText = "color:#16803c;font-weight:700;margin-left:0.25em;";
      link.insertAdjacentElement("afterend", marker);
      link.setAttribute(MARKER_ATTRIBUTE, "true");
    });
  }

  async function main() {
    const cached = readCache();
    try {
      const urls = cached || await requestList();
      addCheckmarks(urls);
      new MutationObserver(() => addCheckmarks(urls)).observe(document.body, {
        childList: true,
        subtree: true,
      });
    } catch (error) {
      console.warn("Motamem checkmarks: using no list", error);
    }
  }

  if (document.body) main();
  else window.addEventListener("DOMContentLoaded", main, { once: true });
})();
