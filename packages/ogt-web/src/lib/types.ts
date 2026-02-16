export interface ScrewSize {
  diameter: number
  head_diameter: number
  head_inset: number
}

export interface SummitFeatures {
  connector_angle: number | null
  tile_chamfer: boolean
  screw: boolean
}

export interface GridPlan {
  tiles: boolean[][]
  summits: SummitFeatures[][]
  opengrid_type: "full" | "light"
  screw_size: ScrewSize
}
