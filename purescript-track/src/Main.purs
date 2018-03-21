module Main where

import Prelude
import Window

import Control.Monad.Eff.Console
import Control.Monad.Eff
import DOM

import Signal
import Signal.Time
import Signal.DOM

import WebSocket

foreign import stringify :: forall a. a -> String

type ArticleID = Int
type Seconds = Int
type Percent = Number

-- | Main data structure for sending information to the server
data Data = Data
  { engagedTime :: Seconds
  , percentRead :: Percent
  }

instance showData :: Show Data where
  show (Data n) = stringify n

emptyData :: Data
emptyData = Data
  { engagedTime: 0
  , percentRead: 0.0
  }

tick :: forall a. Number -> a -> Signal a
tick interval value = sampleOn (every interval) (constant value)

everySecond :: Signal Unit
everySecond = tick 1000.0 unit

mouseMoved :: forall e. Eff (dom :: DOM | e) (Signal Unit)
mouseMoved = do
  mp <- mousePos
  pure $ map (\_ -> unit) (dropRepeats' mp)

recentlyActive :: forall a. Signal a -> Signal Boolean
recentlyActive = since 4600.0

active :: forall e. Eff (dom :: DOM | e) (Signal Boolean)
active = do
  -- `m` represents all the other events
  -- TODO: build up a signal of all other events via `merge`
  m <- mouseMoved
  focused <- windowIsFocused
  pure $ (&&) <$> (recentlyActive m) <*> focused

-- | `Boolean` here is `active`
dataGenF :: Boolean -> Data -> Data
dataGenF isActive d = if isActive == true then incEngagedTime d else d

dataGenerator :: forall e. Eff (dom :: DOM | e) (Signal Data)
dataGenerator = do
  a <- active
  pure $ foldp dataGenF emptyData (sampleOn everySecond a)

incEngagedTime :: Data -> Data
incEngagedTime (Data n) = Data $ n {engagedTime = n.engagedTime + 1}

sendData :: forall e. Socket -> Data -> Eff (ws :: WebSocket | e) Unit
sendData s (Data d) = send s (stringify d)

main :: forall e. Eff (dom :: DOM, ws :: WebSocket | e) Unit
main = do
  d <- dataGenerator
  ws <- mkWebSocket "wss://presence-staging.publet.com/ws/1"

  onOpen ws $ do
    runSignal $ map (sendData ws) $ sampleOn (tick 3000.0 unit ) d
