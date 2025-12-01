import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { formatHMS, parseHMS, secondsClamp, snap, generateTimeOptions } from '@/lib/time';

interface VideoRangeSelectorProps {
  duration: number; // seconds
  value: [number, number]; // [startS, endS]
  onChange: (next: [number, number]) => void;
  step?: number; // default 1s
}

export const VideoRangeSelector: React.FC<VideoRangeSelectorProps> = ({
  duration,
  value: [startS, endS],
  onChange,
  step = 1
}) => {
  const [startTime, setStartTime] = useState({ hours: 0, minutes: 0, seconds: 0 });
  const [endTime, setEndTime] = useState({ hours: 0, minutes: 0, seconds: 0 });

  // Update time pickers when slider changes
  useEffect(() => {
    const startTotal = snap(startS, step);
    const endTotal = snap(endS, step);
    
    setStartTime({
      hours: Math.floor(startTotal / 3600),
      minutes: Math.floor((startTotal % 3600) / 60),
      seconds: Math.floor(startTotal % 60)
    });
    
    setEndTime({
      hours: Math.floor(endTotal / 3600),
      minutes: Math.floor((endTotal % 3600) / 60),
      seconds: Math.floor(endTotal % 60)
    });
  }, [startS, endS, step]);

  // Convert time picker values to seconds
  const timeToSeconds = useCallback((time: { hours: number; minutes: number; seconds: number }) => {
    return time.hours * 3600 + time.minutes * 60 + time.seconds;
  }, []);

  // Handle slider change
  const handleSliderChange = useCallback((newValue: number[]) => {
    const [newStart, newEnd] = newValue;
    // Use smaller step for smoother slider movement
    const smoothStep = 0.01;
    const clampedStart = secondsClamp(snap(newStart, smoothStep), 0, duration);
    const clampedEnd = secondsClamp(snap(newEnd, smoothStep), clampedStart + smoothStep, duration);
    
    onChange([clampedStart, clampedEnd]);
  }, [duration, onChange]);

  // Handle time picker change
  const handleTimeChange = useCallback((
    type: 'start' | 'end',
    field: 'hours' | 'minutes' | 'seconds',
    value: number
  ) => {
    const currentTime = type === 'start' ? startTime : endTime;
    const newTime = { ...currentTime, [field]: value };
    const newSeconds = timeToSeconds(newTime);
    
    if (type === 'start') {
      const clampedStart = secondsClamp(snap(newSeconds, step), 0, duration);
      const clampedEnd = Math.max(clampedStart + step, endS);
      onChange([clampedStart, clampedEnd]);
    } else {
      const clampedEnd = secondsClamp(snap(newSeconds, step), startS + step, duration);
      onChange([startS, clampedEnd]);
    }
  }, [startTime, endTime, startS, endS, duration, step, timeToSeconds, onChange]);

  const hoursOptions = generateTimeOptions(23);
  const minutesOptions = generateTimeOptions(59);
  const secondsOptions = generateTimeOptions(59);

  return (
    <Card className="w-full transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-lg">Analysis Window</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Timeline Range Slider */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Timeline Range</Label>
          <div className="px-2">
            <Slider
              value={[startS, endS]}
              onValueChange={handleSliderChange}
              max={duration}
              step={0.01}
              min={0}
              className="w-full [&_[role=slider]]:transition-all [&_[role=slider]]:duration-100 [&_[role=slider]]:ease-out hover:[&_[role=slider]]:scale-105"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Start: {formatHMS(startS)}</span>
              <span>End: {formatHMS(endS)}</span>
            </div>
          </div>
        </div>

        {/* Time Pickers */}
        <div className="grid grid-cols-2 gap-4">
          {/* Start Time Picker */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Start Time</Label>
            <div className="flex gap-2">
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'hours', Math.min(23, startTime.hours + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={startTime.hours.toString()}
                  onValueChange={(value) => handleTimeChange('start', 'hours', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {hoursOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'hours', Math.max(0, startTime.hours - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
              <span className="flex items-center text-muted-foreground">:</span>
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'minutes', Math.min(59, startTime.minutes + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={startTime.minutes.toString()}
                  onValueChange={(value) => handleTimeChange('start', 'minutes', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {minutesOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'minutes', Math.max(0, startTime.minutes - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
              <span className="flex items-center text-muted-foreground">:</span>
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'seconds', Math.min(59, startTime.seconds + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={startTime.seconds.toString()}
                  onValueChange={(value) => handleTimeChange('start', 'seconds', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {secondsOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('start', 'seconds', Math.max(0, startTime.seconds - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>

          {/* End Time Picker */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">End Time</Label>
            <div className="flex gap-2">
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'hours', Math.min(23, endTime.hours + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={endTime.hours.toString()}
                  onValueChange={(value) => handleTimeChange('end', 'hours', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {hoursOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'hours', Math.max(0, endTime.hours - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
              <span className="flex items-center text-muted-foreground">:</span>
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'minutes', Math.min(59, endTime.minutes + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={endTime.minutes.toString()}
                  onValueChange={(value) => handleTimeChange('end', 'minutes', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {minutesOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'minutes', Math.max(0, endTime.minutes - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
              <span className="flex items-center text-muted-foreground">:</span>
              <div className="flex flex-col items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'seconds', Math.min(59, endTime.seconds + 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <Select
                  value={endTime.seconds.toString()}
                  onValueChange={(value) => handleTimeChange('end', 'seconds', parseInt(value))}
                >
                  <SelectTrigger className="w-16 h-8 transition-all duration-200 hover:scale-105 hover:shadow-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {secondsOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  type="button"
                  onClick={() => handleTimeChange('end', 'seconds', Math.max(0, endTime.seconds - 1))}
                  className="h-4 w-6 flex items-center justify-center hover:bg-gray-100 rounded text-xs transition-all duration-200 hover:scale-110"
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Duration Info */}
        <div className="text-sm text-muted-foreground">
          <div>Selected duration: {formatHMS(endS - startS)}</div>
          <div>Total video duration: {formatHMS(duration)}</div>
        </div>
      </CardContent>
    </Card>
  );
};
