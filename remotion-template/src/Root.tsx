import React from "react";
import { Composition } from "remotion";
import { EpisodeCourse, DURATION_IN_FRAMES } from "./EpisodeCourse";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="EpisodeCourse"
      component={EpisodeCourse}
      durationInFrames={DURATION_IN_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  </>
);
