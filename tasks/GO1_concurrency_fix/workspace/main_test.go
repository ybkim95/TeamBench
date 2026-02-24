package main

import (
	"context"
	"testing"
	"time"
)

// TestProcessJobs verifies that all 10 jobs complete successfully.
func TestProcessJobs(t *testing.T) {
	p := NewProcessor(3)
	for i := 1; i <= 10; i++ {
		p.addJob(Job{ID: i, Payload: "test"})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	results, err := p.processJobs(ctx)
	if err != nil {
		t.Fatalf("processJobs returned error: %v", err)
	}
	if len(results) != 10 {
		t.Fatalf("expected 10 results, got %d", len(results))
	}
}

// TestConcurrentAccess hammers addJob and getStats from multiple goroutines
// to surface data races and lock-ordering deadlocks.
func TestConcurrentAccess(t *testing.T) {
	p := NewProcessor(4)

	done := make(chan struct{})
	go func() {
		for i := 0; i < 50; i++ {
			p.addJob(Job{ID: i, Payload: "concurrent"})
		}
		close(done)
	}()

	go func() {
		for i := 0; i < 50; i++ {
			_ = p.getStats()
		}
	}()

	select {
	case <-done:
		// ok
	case <-time.After(5 * time.Second):
		t.Fatal("TestConcurrentAccess timed out — likely deadlock")
	}
}

// TestContextCancellation verifies that cancelling the context does not leak
// goroutines — the program must not hang after the test function returns.
// With the buggy unbuffered channel, workers block forever on "results <- result"
// once the receiver exits, causing this test to time out.
func TestContextCancellation(t *testing.T) {
	p := NewProcessor(3)
	// Enough jobs that workers will have computed results and be blocked
	// on the unbuffered send when we cancel.
	for i := 1; i <= 30; i++ {
		p.addJob(Job{ID: i, Payload: "cancel-test"})
	}

	ctx, cancel := context.WithCancel(context.Background())
	// Let one batch of workers finish and queue up on the channel before cancel.
	go func() {
		time.Sleep(15 * time.Millisecond)
		cancel()
	}()

	done := make(chan struct{})
	go func() {
		p.processJobs(ctx) //nolint:errcheck
		close(done)
	}()

	select {
	case <-done:
		// Good — returned without hanging.
	case <-time.After(5 * time.Second):
		t.Fatal("TestContextCancellation timed out — goroutine leak suspected")
	}
}
