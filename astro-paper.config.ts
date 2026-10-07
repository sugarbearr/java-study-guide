import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: "https://sugarbearr.github.io/java-study-guide/",
    title: "Java 入门到面试指南",
    description:
      "基于廖雪峰教程、慕课网、JavaGuide、pdai.tech、码工具五大站点整合的 Java 后端自学路线：入门、并发与 JVM、数据库、中间件、分布式，配套章节小考、综合大考与八股闪卡。",
    author: "sugarbearr",
    profile: "https://github.com/sugarbearr",
    ogImage: "default-og.jpg",
    lang: "zh-cn",
    timezone: "Asia/Shanghai",
    dir: "ltr",
  },
  posts: {
    perPage: 8,
    perIndex: 6,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: false,
    showArchives: true,
    showBackButton: true,
    editPost: {
      enabled: false,
    },
    search: "pagefind",
  },
  socials: [
    { name: "github", url: "https://github.com/sugarbearr/java-study-guide" },
  ],
  shareLinks: [],
});
