/**
 * E24《大觉寺·阳台山麓的千年清水院》分层视口引擎 (Layered Viewport Engine) 导出包。
 * 复用并特化自 E20 勺园视口引擎，
 * 见 docs/superpowers/specs/2026-10-03-e21-dajuesi-design.md §2.1。
 *
 * 红线：本包只导出视口与 SVG 叠加层组件，严禁向 slots.json 导出任何文字槽；
 * 浮于视口之上的文字卡片一律由 data/slots.json 承载并配置 backing: true。
 */
export { PanZoomView } from "./PanZoomView";
export type { ViewSpec } from "./PanZoomView";
export { CrossFadeViewport } from "./CrossFadeViewport";
export type { CrossFadeLayer } from "./CrossFadeViewport";
export { ScrollPanView } from "./ScrollPanView";
export { MapMarker } from "./MapMarker";
