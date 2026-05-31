import React from "react";
import { Composition } from "remotion";
import { ZiaCarousel, ZiaCarouselProps, defaultZiaCarouselProps } from "./ZiaCarousel";
import { ZiaStory, ZiaStoryProps, defaultZiaStoryProps } from "./ZiaStory";

const FPS = 30;
const CAROUSEL_FRAMES = 6 * 140 - 5 * 25; // 715
const STORY_FRAMES = 300; // 10s

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="ZiaCarousel"
      component={ZiaCarousel}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={CAROUSEL_FRAMES}
      defaultProps={defaultZiaCarouselProps}
    />
    <Composition
      id="ZiaStory"
      component={ZiaStory}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={STORY_FRAMES}
      defaultProps={defaultZiaStoryProps}
    />
  </>
);
