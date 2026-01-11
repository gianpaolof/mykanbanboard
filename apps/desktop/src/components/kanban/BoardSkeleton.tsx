// components/kanban/BoardSkeleton.tsx - Loading skeleton for the board
import { memo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const SkeletonCard = memo(function SkeletonCard({
  delay,
}: {
  delay: number;
}) {
  return (
    <motion.div
      animate={{
        opacity: [0.5, 0.8, 0.5],
      }}
      transition={{
        repeat: Infinity,
        duration: 1.5,
        delay,
        ease: 'easeInOut',
      }}
      className={cn(
        'rounded-xl p-3 h-24',
        'bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.04)]'
      )}
    >
      {/* Title placeholder */}
      <div className="h-4 w-3/4 bg-zinc-800/50 rounded mb-3" />
      {/* Labels placeholder */}
      <div className="flex gap-1.5">
        <div className="h-3 w-12 bg-zinc-800/50 rounded" />
        <div className="h-3 w-16 bg-zinc-800/50 rounded" />
      </div>
    </motion.div>
  );
});

const SkeletonColumn = memo(function SkeletonColumn({
  columnIndex,
}: {
  columnIndex: number;
}) {
  const cardCount = 3 - (columnIndex % 2); // Vary cards per column

  return (
    <div className="w-[300px] flex-shrink-0 flex flex-col">
      {/* Column header skeleton */}
      <div className="flex items-center gap-2 px-1 py-2 mb-3">
        <motion.div
          animate={{ opacity: [0.5, 0.8, 0.5] }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            delay: columnIndex * 0.1,
            ease: 'easeInOut',
          }}
          className="w-2.5 h-2.5 rounded-full bg-zinc-800"
        />
        <motion.div
          animate={{ opacity: [0.5, 0.8, 0.5] }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            delay: columnIndex * 0.1 + 0.05,
            ease: 'easeInOut',
          }}
          className="h-4 w-24 bg-zinc-800 rounded"
        />
        <motion.div
          animate={{ opacity: [0.5, 0.8, 0.5] }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            delay: columnIndex * 0.1 + 0.1,
            ease: 'easeInOut',
          }}
          className="h-4 w-8 bg-zinc-800 rounded"
        />
      </div>

      {/* Card skeletons */}
      <div className="space-y-2">
        {Array.from({ length: cardCount }).map((_, cardIndex) => (
          <SkeletonCard
            key={cardIndex}
            delay={(columnIndex + cardIndex) * 0.1}
          />
        ))}
      </div>
    </div>
  );
});

export const BoardSkeleton = memo(function BoardSkeleton() {
  return (
    <div className="flex gap-4 h-full overflow-x-auto p-4">
      {[0, 1, 2, 3, 4].map((columnIndex) => (
        <SkeletonColumn key={columnIndex} columnIndex={columnIndex} />
      ))}
    </div>
  );
});
