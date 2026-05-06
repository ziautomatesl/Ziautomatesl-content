import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { ZiaVideo, ZiaVideoProps, defaultZiaVideoProps } from "./ZiaVideo";

const FPS = 30;

const calculateMetadata: CalculateMetadataFunction<ZiaVideoProps> = async ({ props }) => {
  return {
    durationInFrames: Math.ceil(props.durationInSeconds * FPS),
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ZiaVideo"
      component={ZiaVideo}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={defaultZiaVideoProps}
      calculateMetadata={calculateMetadata}
    />
  );
};
