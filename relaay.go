package main

import (
	"bytes"
	"log"
	"sync"
	"time"

	"github.com/valyala/fasthttp"
)

type Message struct {
	Data []byte
	Time time.Time
}

type RelayServer struct {
	serverQueue  chan Message
	clientQueue  chan Message
	isServerConn bool
	isClientConn bool
	mu           sync.Mutex
}

func NewRelayServer() *RelayServer {
	return &RelayServer{
		serverQueue:  make(chan Message, 100),
		clientQueue:  make(chan Message, 100),
		isServerConn: false,
		isClientConn: false,
	}
}

func (rs *RelayServer) HandleServerPoll(ctx *fasthttp.RequestCtx) {
	rs.mu.Lock()
	rs.isServerConn = true
	rs.mu.Unlock()

	select {
	case msg := <-rs.serverQueue:
		ctx.SetBody(msg.Data)
	case <-time.After(30 * time.Second):
		ctx.SetStatusCode(fasthttp.StatusNoContent)
	}
}

func (rs *RelayServer) HandleClientPoll(ctx *fasthttp.RequestCtx) {
	rs.mu.Lock()
	rs.isClientConn = true
	rs.mu.Unlock()

	select {
	case msg := <-rs.clientQueue:
		ctx.SetBody(msg.Data)
	case <-time.After(30 * time.Second):
		ctx.SetStatusCode(fasthttp.StatusNoContent)
	}
}

func (rs *RelayServer) HandleServerPush(ctx *fasthttp.RequestCtx) {
	body := ctx.PostBody()
	if len(body) > 0 {
		rs.clientQueue <- Message{
			Data: bytes.Clone(body),
			Time: time.Now(),
		}
		ctx.SetStatusCode(fasthttp.StatusOK)
	} else {
		ctx.SetStatusCode(fasthttp.StatusBadRequest)
	}
}

func (rs *RelayServer) HandleClientPush(ctx *fasthttp.RequestCtx) {
	body := ctx.PostBody()
	if len(body) > 0 {
		rs.serverQueue <- Message{
			Data: bytes.Clone(body),
			Time: time.Now(),
		}
		ctx.SetStatusCode(fasthttp.StatusOK)
	} else {
		ctx.SetStatusCode(fasthttp.StatusBadRequest)
	}
}

func main() {
	relay := NewRelayServer()

	router := func(ctx *fasthttp.RequestCtx) {
		path := string(ctx.Path())
		switch {
		case path == "/server/poll" && ctx.IsGet():
			relay.HandleServerPoll(ctx)
		case path == "/client/poll" && ctx.IsGet():
			relay.HandleClientPoll(ctx)
		case path == "/server/push" && ctx.IsPost():
			relay.HandleServerPush(ctx)
		case path == "/client/push" && ctx.IsPost():
			relay.HandleClientPush(ctx)
		default:
			ctx.Error("Not found", fasthttp.StatusNotFound)
		}
	}

	log.Println("Starting relay server on :8080")
	if err := fasthttp.ListenAndServe(":8080", router); err != nil {
		log.Fatalf("Error in relay server: %v", err)
	}
}
