## Module Main

#### `stringify`

``` purescript
stringify :: forall a. a -> String
```

#### `ArticleID`

``` purescript
type ArticleID = Int
```

#### `Seconds`

``` purescript
type Seconds = Int
```

#### `Percent`

``` purescript
type Percent = Number
```

#### `Data`

``` purescript
data Data
  = Data { engagedTime :: Seconds, percentRead :: Percent }
```

Main data structure for sending information to the server

##### Instances
``` purescript
instance showData :: Show Data
```

#### `emptyData`

``` purescript
emptyData :: Data
```

#### `tick`

``` purescript
tick :: forall a. Number -> a -> Signal a
```

#### `everySecond`

``` purescript
everySecond :: Signal Unit
```

#### `websocketEff`

``` purescript
websocketEff :: forall e. Socket -> Signal (Eff (ws :: WebSocket | e) Unit)
```

#### `mouseMoved`

``` purescript
mouseMoved :: forall e. Eff (dom :: DOM | e) (Signal Unit)
```

#### `recentlyActive`

``` purescript
recentlyActive :: forall a. Signal a -> Signal Boolean
```

#### `active`

``` purescript
active :: forall e. Eff (dom :: DOM | e) (Signal Boolean)
```

#### `dataGenF`

``` purescript
dataGenF :: Boolean -> Data -> Data
```

`Boolean` here is `active`

#### `dataGenerator`

``` purescript
dataGenerator :: forall e. Eff (dom :: DOM | e) (Signal Data)
```

#### `incEngagedTime`

``` purescript
incEngagedTime :: Data -> Data
```

#### `sendData`

``` purescript
sendData :: forall e. Socket -> Data -> Eff (ws :: WebSocket | e) Unit
```


