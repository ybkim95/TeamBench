package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Job represents a unit of work.
type Job struct {
	ID      int
	Payload string
}

// Result holds the outcome of a processed job.
type Result struct {
	JobID    int
	WorkerID int
	Output   string
}

// JobProcessor manages a pool of workers that process jobs concurrently.
type JobProcessor struct {
	workers int
	queue   []Job
	stats   map[int]int // per-worker completion counts
	mu1     sync.Mutex  // protects queue
	mu2     sync.Mutex  // protects stats
}

// NewProcessor creates a JobProcessor with the given number of workers.
func NewProcessor(workers int) *JobProcessor {
	return &JobProcessor{
		workers: workers,
		queue:   make([]Job, 0),
		stats:   make(map[int]int),
	}
}

// addJob appends a job to the queue and updates the stats entry for bookkeeping.
// BUG 3: acquires mu1 then mu2 — opposite order from getStats (mu2 then mu1).
func (p *JobProcessor) addJob(job Job) {
	p.mu1.Lock()
	p.queue = append(p.queue, job)
	p.mu2.Lock()
	// initialise stats slot so workers don't have to create it
	if _, ok := p.stats[job.ID%p.workers]; !ok {
		p.stats[job.ID%p.workers] = 0
	}
	p.mu2.Unlock()
	p.mu1.Unlock()
}

// getStats returns a snapshot of per-worker completion counts.
// BUG 3: acquires mu2 then mu1 — opposite order from addJob (mu1 then mu2).
func (p *JobProcessor) getStats() map[int]int {
	p.mu2.Lock()
	defer p.mu2.Unlock()
	p.mu1.Lock()
	defer p.mu1.Unlock()

	snapshot := make(map[int]int, len(p.stats))
	for k, v := range p.stats {
		snapshot[k] = v
	}
	return snapshot
}

// worker pulls jobs from the jobs channel and sends results to results channel.
// BUG 1: writes p.stats[id]++ without holding mu2 — data race with other workers.
func (p *JobProcessor) worker(id int, jobs <-chan Job, results chan<- Result) {
	for job := range jobs {
		// Simulate work.
		time.Sleep(time.Millisecond * 10)

		// BUG 1: unsynchronised write to shared map.
		p.stats[id]++

		results <- Result{
			JobID:    job.ID,
			WorkerID: id,
			Output:   fmt.Sprintf("job-%d done by worker-%d", job.ID, id),
		}
	}
}

// processJobs distributes queued jobs across workers and collects results.
// BUG 2: results channel is unbuffered; if ctx is cancelled the receive loop
// exits early, leaving workers blocked forever on "results <- result".
func (p *JobProcessor) processJobs(ctx context.Context) ([]Result, error) {
	p.mu1.Lock()
	jobs := make([]Job, len(p.queue))
	copy(jobs, p.queue)
	p.mu1.Unlock()

	jobCh := make(chan Job, len(jobs))
	// BUG 2: unbuffered — senders block if receiver stops early.
	results := make(chan Result)

	var wg sync.WaitGroup
	for i := 0; i < p.workers; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			p.worker(id, jobCh, results)
		}(i)
	}

	// Feed jobs.
	go func() {
		for _, j := range jobs {
			jobCh <- j
		}
		close(jobCh)
	}()

	// Close results once all workers finish.
	go func() {
		wg.Wait()
		close(results)
	}()

	var collected []Result
	for {
		select {
		case res, ok := <-results:
			if !ok {
				return collected, nil
			}
			collected = append(collected, res)
		case <-ctx.Done():
			// BUG 2: returns immediately, leaving workers blocked on results<-result.
			return collected, ctx.Err()
		}
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	p := NewProcessor(3)

	for i := 1; i <= 10; i++ {
		p.addJob(Job{ID: i, Payload: fmt.Sprintf("payload-%d", i)})
	}

	results, err := p.processJobs(ctx)
	if err != nil {
		fmt.Printf("processing error: %v\n", err)
		return
	}

	fmt.Printf("All %d jobs completed\n", len(results))

	stats := p.getStats()
	for workerID, count := range stats {
		fmt.Printf("Worker %d: %d jobs\n", workerID, count)
	}
}
