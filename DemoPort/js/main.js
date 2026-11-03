(function () {
  const P = window.PROFILE;
  const $ = (sel) => document.querySelector(sel);

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "text") node.textContent = v;
      else if (k === "class") node.className = v;
      else node.setAttribute(k, v);
    }
    for (const child of [].concat(children)) if (child) node.append(child);
    return node;
  }

  const categoryTitle = Object.fromEntries(P.expertise.map((e) => [e.id, e.title]));

  // 단순 텍스트 바인딩
  document.querySelectorAll("[data-bind]").forEach((node) => {
    node.textContent = P[node.dataset.bind] || "";
  });
  document.title = `${P.name} | HRD 전문가 프로필`;
  $("#year").textContent = new Date().getFullYear();

  // Hero 태그
  P.expertise.forEach((e) => $("#heroTags").append(el("li", { text: e.title })));

  // About
  const photo = $("#aboutPhoto");
  if (P.photo) photo.append(el("img", { src: P.photo, alt: `${P.name} 프로필 사진` }));
  else {
    photo.textContent = (P.nameEn || P.name).replace(/[\[\]]/g, "").charAt(0) || "H";
    photo.setAttribute("aria-hidden", "true");
  }
  P.about.paragraphs.forEach((t) => $("#aboutText").append(el("p", { text: t })));
  P.about.values.forEach((v) =>
    $("#values").append(el("li", {}, [el("strong", { text: v.title }), el("span", { text: v.desc })]))
  );

  // Expertise
  P.expertise.forEach((e) => {
    $("#expertiseGrid").append(
      el("article", { class: "card exp-card reveal" }, [
        el("div", { class: "exp-icon", "aria-hidden": "true", text: e.icon }),
        el("h3", { text: e.title }),
        el("p", { text: e.desc }),
        el("ul", {}, e.items.map((i) => el("li", { text: i }))),
      ])
    );
  });

  // Experience
  P.experience.forEach((x) => {
    $("#timeline").append(
      el("li", { class: "reveal" }, [
        el("div", { class: "tl-period", text: x.period }),
        el("div", { class: "tl-org", text: x.org }),
        el("div", { class: "tl-role", text: x.role }),
        el("ul", { class: "tl-achievements" }, x.achievements.map((a) => el("li", { text: a }))),
      ])
    );
  });

  // Projects + filters
  function renderProjects(filter) {
    const grid = $("#projectGrid");
    grid.replaceChildren();
    P.projects
      .filter((p) => filter === "all" || p.category === filter)
      .forEach((p) => {
        const detail = el("dl", { class: "project-detail" });
        [["기획 의도", p.intent], ["진행 방식", p.method], ["성과", p.result]].forEach(([k, v]) => {
          if (v) detail.append(el("dt", { text: k }), el("dd", { text: v }));
        });
        grid.append(
          el("article", { class: "card project-card" }, [
            el("div", { class: "project-head" }, [
              el("h3", { text: p.title }),
              el("span", { class: "badge", text: categoryTitle[p.category] || p.category }),
            ]),
            el("div", { class: "project-meta" }, [
              el("span", { text: `대상 ${p.target}` }),
              el("span", { text: `기간 ${p.period}` }),
              el("span", { text: `역할 ${p.role}` }),
            ]),
            detail,
          ])
        );
      });
  }

  const filters = [{ id: "all", title: "전체" }, ...P.expertise];
  filters.forEach((f, i) => {
    const btn = el("button", {
      class: "filter-btn",
      type: "button",
      role: "tab",
      "aria-selected": String(i === 0),
      "data-filter": f.id,
      text: f.title,
    });
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach((b) => b.setAttribute("aria-selected", String(b === btn)));
      renderProjects(f.id);
    });
    $("#filters").append(btn);
  });
  renderProjects("all");

  // Credentials
  const credItem = (c) => el("li", {}, [c.title, el("span", { text: c.meta })]);
  P.education.forEach((c) => $("#educationList").append(credItem(c)));
  P.certifications.forEach((c) => $("#certList").append(credItem(c)));

  // Contact
  const mail = $("#mailLink");
  mail.href = `mailto:${P.email}`;
  mail.textContent = P.email;
  $("#copyEmail").addEventListener("click", async () => {
    const msg = $("#copyMsg");
    try {
      await navigator.clipboard.writeText(P.email);
      msg.textContent = "이메일 주소가 복사되었습니다.";
    } catch {
      msg.textContent = `복사에 실패했습니다. 직접 복사해 주세요: ${P.email}`;
    }
    setTimeout(() => (msg.textContent = ""), 2500);
  });
  P.links.forEach((l) =>
    $("#extLinks").append(el("li", {}, el("a", { href: l.url, target: "_blank", rel: "noopener", text: l.label })))
  );

  // Nav: 스크롤 테두리 + 모바일 메뉴
  const nav = $("#nav");
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const toggle = $("#navToggle");
  const links = $("#navLinks");
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  links.addEventListener("click", (e) => {
    if (e.target.tagName === "A") {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });

  // 스크롤 등장 애니메이션
  const io = new IntersectionObserver(
    (entries) => entries.forEach((en) => en.isIntersecting && (en.target.classList.add("visible"), io.unobserve(en.target))),
    { threshold: 0.15 }
  );
  document.querySelectorAll(".reveal").forEach((n) => io.observe(n));
})();
