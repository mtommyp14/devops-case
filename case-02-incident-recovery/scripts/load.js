import http from 'k6/http';
import { check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const offeredRequests = new Counter('offered_requests');
const successfulRequests = new Counter('successful_requests');
const controlledRejections = new Counter('controlled_rejections');
const unexpectedFailures = new Counter('unexpected_failures');
const successfulRequestDuration = new Trend('successful_request_duration', true);

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 20),
      timeUnit: '1s',
      duration: __ENV.DURATION || '130s',
      preAllocatedVUs: Number(__ENV.PREALLOCATED_VUS || 100),
      maxVUs: Number(__ENV.MAX_VUS || 400),
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  offeredRequests.add(1);
  const priority = __ITER % 10 === 0 ? 'critical' : 'low';
  const response = http.get(`http://router:8000/api/work?priority=${priority}`, { tags: { priority } });
  const loadShed = response.headers['X-Load-Shed'] === 'true' || response.headers['x-load-shed'] === 'true';
  const successful = response.status === 200;
  const rejectedByLoadShedding = [429, 503].includes(response.status) && loadShed;

  if (successful) {
    successfulRequests.add(1);
    successfulRequestDuration.add(response.timings.duration);
  } else if (rejectedByLoadShedding) {
    controlledRejections.add(1);
  } else {
    unexpectedFailures.add(1);
  }

  check(response, { 'successful or controlled load-shed response': () => successful || rejectedByLoadShedding });
}
