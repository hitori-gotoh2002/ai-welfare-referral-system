(() => {
  if (typeof state === "undefined") return;

  function hasStructuredCase() {
    return Boolean(state.structured);
  }

  function ensurePackageReady({ asyncRefresh = true, show = false } = {}) {
    if (!hasStructuredCase()) return;
    let needsRefresh = false;

    if (!Array.isArray(state.packages) || !state.packages.length) {
      generatePackagesLocal({ show });
      state.selectedPackageId = state.packages[0]?.id || null;
      needsRefresh = true;
    } else if (!state.selectedPackageId) {
      state.selectedPackageId = state.packages[0]?.id || null;
    }

    if (asyncRefresh && needsRefresh) {
      Promise.resolve(generatePackages({})).catch(() => {
        render();
      });
    }
  }

  const nativeInferStructure = inferStructure;
  inferStructure = async function patchedInferStructureAutoPackage(options = {}) {
    const nextView = options.goTo;
    await nativeInferStructure({ ...options, goTo: undefined });
    ensurePackageReady({ asyncRefresh: true, show: false });
    if (nextView) {
      setView(nextView);
    } else {
      render();
    }
  };

  const nativeInferStructureLocal = inferStructureLocal;
  inferStructureLocal = function patchedInferStructureLocalAutoPackage(options = {}) {
    const result = nativeInferStructureLocal(options);
    ensurePackageReady({ asyncRefresh: false, show: false });
    return result;
  };

  const nativeSetView = setView;
  setView = function patchedSetViewAutoPackage(view) {
    if ((view === "search" || view === "packages" || view === "report") && hasStructuredCase()) {
      ensurePackageReady({ asyncRefresh: view === "search", show: false });
    }
    return nativeSetView(view);
  };
})();
