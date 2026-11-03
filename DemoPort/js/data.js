// 사이트 콘텐츠 데이터 — 이 파일만 수정하면 내용이 바뀝니다.
// [ ] 로 표시된 값은 실제 내용으로 교체해 주세요.
window.PROFILE = {
  name: "[이름]",
  nameEn: "[Name]",
  headline: "사람과 조직의 성장을 설계하는 HRD 전문가",
  summary:
    "교육 요구분석부터 과정 설계, 현장 진행, 성과 평가까지 — 배움이 실제 변화로 이어지도록 설계하고 함께 만들어 갑니다.",
  email: "ryoojh@gmail.com",
  photo: "", // 예: "images/profile.jpg" (비워두면 이니셜 표시)
  links: [
    // { label: "LinkedIn", url: "https://www.linkedin.com/in/..." },
  ],

  about: {
    paragraphs: [
      "[자기소개 1] HRD 분야에서 어떤 경험을 쌓아왔는지, 어떤 문제를 해결해 왔는지 적어 주세요.",
      "[자기소개 2] 교육과 조직문화에 대한 나만의 철학, 일하는 방식을 적어 주세요.",
    ],
    values: [
      { title: "현장 중심", desc: "학습자와 조직의 실제 문제에서 출발합니다." },
      { title: "변화 지향", desc: "교육이 행동과 성과의 변화로 이어지도록 설계합니다." },
      { title: "함께 성장", desc: "참여와 소통으로 배움이 일어나는 장을 만듭니다." },
    ],
  },

  expertise: [
    {
      id: "hrd",
      title: "HRD",
      icon: "🌱",
      desc: "조직의 전략과 연계된 인재육성 체계를 수립합니다.",
      items: ["인재육성 체계 수립", "역량 모델링", "경력개발 프로그램"],
    },
    {
      id: "planning",
      title: "교육기획",
      icon: "🧭",
      desc: "요구분석에 기반해 목적이 분명한 교육과정을 설계합니다.",
      items: ["교육 요구분석(TNA)", "교육과정 설계 (ADDIE)", "커리큘럼 개발", "교육 효과성 평가"],
    },
    {
      id: "delivery",
      title: "교육진행",
      icon: "🎤",
      desc: "참여와 몰입을 이끌어내는 강의와 워크숍을 진행합니다.",
      items: ["강의 · 워크숍 퍼실리테이션", "신입사원 교육", "리더십 교육 운영"],
    },
    {
      id: "culture",
      title: "조직문화",
      icon: "🤝",
      desc: "구성원이 함께 일하고 싶은 조직문화를 만들어 갑니다.",
      items: ["조직진단", "핵심가치 내재화", "소통 · 협업 문화 개선"],
    },
  ],

  experience: [
    {
      period: "[20XX.XX – 현재]",
      org: "[소속 기관 / 회사]",
      role: "[직무 / 직책]",
      achievements: ["[주요 성과 1 — 예: 연간 OO개 과정 기획·운영, 만족도 4.6/5.0]", "[주요 성과 2]"],
    },
    {
      period: "[20XX.XX – 20XX.XX]",
      org: "[소속 기관 / 회사]",
      role: "[직무 / 직책]",
      achievements: ["[주요 성과 1]", "[주요 성과 2]"],
    },
  ],

  // category: expertise의 id 값 (hrd | planning | delivery | culture)
  projects: [
    {
      title: "[신입사원 온보딩 프로그램]",
      category: "planning",
      target: "[신입사원 OO명]",
      period: "[20XX.XX]",
      role: "[기획 · 운영]",
      intent: "[기획 의도 — 어떤 문제를 해결하려 했는지]",
      method: "[진행 방식 — 예: 3일 과정, 액션러닝 기반]",
      result: "[성과 — 예: 만족도 4.7/5.0, 조기 퇴사율 감소]",
    },
    {
      title: "[리더십 역량 강화 워크숍]",
      category: "delivery",
      target: "[팀장급 OO명]",
      period: "[20XX.XX]",
      role: "[퍼실리테이터]",
      intent: "[기획 의도]",
      method: "[진행 방식]",
      result: "[성과]",
    },
    {
      title: "[핵심가치 내재화 프로젝트]",
      category: "culture",
      target: "[전 직원 OO명]",
      period: "[20XX.XX – 20XX.XX]",
      role: "[PM]",
      intent: "[기획 의도]",
      method: "[진행 방식]",
      result: "[성과]",
    },
    {
      title: "[직무 역량 모델링]",
      category: "hrd",
      target: "[OO 직군]",
      period: "[20XX.XX]",
      role: "[역량 모델 설계]",
      intent: "[기획 의도]",
      method: "[진행 방식]",
      result: "[성과]",
    },
  ],

  education: [
    { title: "[OO대학교 OO학과 학사/석사]", meta: "[20XX]" },
  ],
  certifications: [
    { title: "[자격증명]", meta: "[발급기관 · 20XX]" },
  ],
};
