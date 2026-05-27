import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { ZiaVideo, ZiaVideoProps, defaultZiaVideoProps } from "./ZiaVideo";
import { ZiaCarousel, ZiaCarouselProps, defaultZiaCarouselProps } from "./ZiaCarousel";
import { ZiaStory, ZiaStoryProps, defaultZiaStoryProps } from "./ZiaStory";

const FPS = 30;
const CAROUSEL_FRAMES = 6 * 140 - 5 * 25; // 715
const STORY_FRAMES = 300; // 10s

const calculateVideoMetadata: CalculateMetadataFunction<ZiaVideoProps> = async ({ props }) => ({
  durationInFrames: Math.ceil(props.durationInSeconds * FPS),
});

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="ZiaVideo"
      component={ZiaVideo}
      fps={24}
      width={1080}
      height={1920}
      defaultProps={defaultZiaVideoProps}
      calculateMetadata={calculateVideoMetadata}
    />
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
