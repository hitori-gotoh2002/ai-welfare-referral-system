(() => {
  if (typeof state === "undefined" || typeof services === "undefined") return;

  const ageTargetPatterns = {
    아동: /아동|영유아|유아|어린이|초등학생|초등|미취학/,
    청소년: /청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원/,
    청년: /청년|대학생|취업준비|구직청년/,
    중장년: /중장년|장년|중년/,
    노인: /노인|어르신|고령|독거노인|독거\s*어르신|65\s*세\s*이상/,
  };
  const broadTargetPattern = /전\s*국민|전체|누구나|저소득|취약계층|위기가구|가구|가족|장애|한부모|기초생활|차상위/;

  function ageGroupsFromText(text) {
    const value = String(text || "");
    const groups = new Set();
    Object.entries(ageTargetPatterns).forEach(([group, pattern]) => {
      if (pattern.test(value)) groups.add(group);
    });
    for (const match of value.matchAll(/(?<!\d)(\d{1,3})\s*세/g)) {
      const age = Number(match[1]);
      if (age < 13) groups.add("아동");
      else if (age < 19) groups.add("청소년");
      else if (age < 40) groups.add("청년");
      else if (age >= 65) groups.add("노인");
      else groups.add("중장년");
    }
    return groups;
  }

  function currentCaseAgeGroups() {
    const primary = ageGroupsFromText([state.case?.title, state.case?.memo].filter(Boolean).join(" "));
    if (primary.size) return primary;
    const structured = ageGroupsFromText(state.structured?.target || "");
    if (structured.size) return structured;
    return ageGroupsFromText(state.case?.targetType || "");
  }

  function serviceAgeGroups(service) {
    return ageGroupsFromText([
      service?.name,
      service?.target,
      service?.summary,
      service?.eligibility,
    ].filter(Boolean).join(" "));
  }

  function serviceMatchesCaseTarget(service) {
    const caseGroups = currentCaseAgeGroups();
    if (!caseGroups.size) return true;
    const targetText = [service?.name, service?.target, service?.summary, service?.eligibility].filter(Boolean).join(" ");
    const targetGroups = serviceAgeGroups(service);
    if (!targetGroups.size || broadTargetPattern.test(targetText)) return true;
    return [...caseGroups].some((group) => targetGroups.has(group));
  }

  function scoreService(service, needs) {
    if (!serviceMatchesCaseTarget(service)) return -1;
    const domains = Array.isArray(service.domains) ? service.domains : [];
    const overlap = domains.filter((domain) => needs.includes(domain)).length;
    const urgent = service.urgency === "긴급" ? 1 : 0;
    const region = state.case?.region && (service.region === "전국" || state.case.region.includes(service.region)) ? 1 : 0;
    const targetBonus = serviceAgeGroups(service).size ? 2 : 0;
    return overlap * 4 + urgent * 2 + region + targetBonus;
  }

  function compatibleRankedServices(needs) {
    return services
      .map((service) => ({ service, score: scoreService(service, needs) }))
      .filter((item) => item.score >= 0)
      .sort((a, b) => b.score - a.score)
      .map((item) => item.service);
  }

  function filterPackageItems(items, needs) {
    const selected = (items || []).filter((item) => {
      const service = services.find((entry) => entry.id === item.serviceId);
      return service && serviceMatchesCaseTarget(service);
    });
    const selectedIds = new Set(selected.map((item) => item.serviceId));
    const domains = new Set(
      selected
        .map((item) => services.find((service) => service.id === item.serviceId))
        .filter(Boolean)
        .flatMap((service) => service.domains || [])
    );
    const ranked = compatibleRankedServices(needs);

    needs.slice(0, 4).forEach((need) => {
      if (domains.has(need)) return;
      const found = ranked.find((service) => (service.domains || []).includes(need) && !selectedIds.has(service.id));
      if (!found) return;
      selected.push({ serviceId: found.id, included: true });
      selectedIds.add(found.id);
      (found.domains || []).forEach((domain) => domains.add(domain));
    });

    while (selected.length < 3) {
      const found = ranked.find((service) => !selectedIds.has(service.id));
      if (!found) break;
      selected.push({ serviceId: found.id, included: true });
      selectedIds.add(found.id);
    }

    return selected.slice(0, 5);
  }

  function filterStatePackages() {
    if (!Array.isArray(state.packages) || !state.packages.length) return;
    const needs = state.structured?.needs?.length ? state.structured.needs : state.case?.issueTypes || [];
    state.packages = state.packages.map((pkg) => ({
      ...pkg,
      items: filterPackageItems(pkg.items, needs),
    }));
    if (!state.packages.some((pkg) => pkg.id === state.selectedPackageId)) {
      state.selectedPackageId = state.packages[0]?.id || null;
    }
  }

  const nativeGeneratePackagesLocal = generatePackagesLocal;
  generatePackagesLocal = function patchedGeneratePackagesLocal(options) {
    const result = nativeGeneratePackagesLocal(options);
    filterStatePackages();
    return result;
  };

  const nativeGeneratePackages = generatePackages;
  generatePackages = async function patchedGeneratePackages(options = {}) {
    const result = await nativeGeneratePackages(options);
    filterStatePackages();
    render();
    return result;
  };

  const nativeAddServiceToPackage = addServiceToPackage;
  addServiceToPackage = function patchedAddServiceToPackage(serviceId) {
    const service = services.find((entry) => entry.id === serviceId);
    if (service && !serviceMatchesCaseTarget(service)) {
      showToast("상담 대상 연령대와 맞지 않는 서비스는 패키지에 추가하지 않았습니다.");
      return;
    }
    nativeAddServiceToPackage(serviceId);
    filterStatePackages();
  };

  const nativeRender = render;
  render = function patchedRender() {
    filterStatePackages();
    return nativeRender();
  };

  filterStatePackages();
})();
