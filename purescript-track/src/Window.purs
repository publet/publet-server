module Window (windowIsFocused) where

import Prelude

import Control.Monad.Eff
import DOM

import Signal

type EventName = String

foreign import windowSignalImpl :: forall e c. (c -> Signal c)
                                   -> EventName
                                   -> Eff (dom :: DOM | e) (Signal Boolean)

windowSignal :: forall e. EventName -> Eff (dom :: DOM | e) (Signal Boolean)
windowSignal = windowSignalImpl constant

windowFocus :: forall e. Eff (dom :: DOM | e) (Signal Boolean)
windowFocus = windowSignal "focus"

windowBlur :: forall e. Eff (dom :: DOM | e) (Signal Boolean)
windowBlur = windowSignal "blur"

-- | yields `true` when the `window` object is focused
windowIsFocused :: forall e. Eff (dom :: DOM | e) (Signal Boolean)
windowIsFocused = do
  f <- windowFocus
  b <- windowBlur
  pure $ merge f (map not b)
