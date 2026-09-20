import Foundation
import HealthKit

struct BiteLogHealthSnapshot: Codable {
    let date: String
    let activeCalories: Int
    let steps: Int
    let workoutMinutes: Int
    let latestHeartRate: Int?
    let warnings: [String]
}

final class HealthKitManager {
    static let shared = HealthKitManager()
    private let store = HKHealthStore()

    private var readTypes: Set<HKObjectType> {
        var types = Set<HKObjectType>()
        if let active = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) { types.insert(active) }
        if let steps = HKObjectType.quantityType(forIdentifier: .stepCount) { types.insert(steps) }
        if let heartRate = HKObjectType.quantityType(forIdentifier: .heartRate) { types.insert(heartRate) }
        types.insert(HKObjectType.workoutType())
        return types
    }

    func requestAuthorization(completion: @escaping (Result<Void, Error>) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(.failure(Self.error("Apple Health is not available on this device.")))
            return
        }

        store.requestAuthorization(toShare: [], read: readTypes) { success, error in
            if let error {
                completion(.failure(error))
            } else if success {
                completion(.success(()))
            } else {
                completion(.failure(Self.error("Apple Health authorization was not completed.")))
            }
        }
    }

    func authorizationRequestStatus(completion: @escaping (Result<String, Error>) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(.success("unavailable"))
            return
        }
        store.getRequestStatusForAuthorization(toShare: [], read: readTypes) { status, error in
            if let error { completion(.failure(error)); return }
            let value: String
            switch status {
            case .shouldRequest: value = "shouldRequest"
            case .unnecessary: value = "unnecessary"
            case .unknown: value = "unknown"
            @unknown default: value = "unknown"
            }
            completion(.success(value))
        }
    }

    func snapshotForToday(completion: @escaping (BiteLogHealthSnapshot) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(BiteLogHealthSnapshot(date: Self.dayString(Date()), activeCalories: 0, steps: 0, workoutMinutes: 0, latestHeartRate: nil, warnings: ["Apple Health is unavailable on this device."]))
            return
        }

        let calendar = Calendar.current
        let start = calendar.startOfDay(for: Date())
        let end = Date()
        let group = DispatchGroup()
        let lock = NSLock()

        var activeCalories: Double = 0
        var steps: Double = 0
        var workoutMinutes: Double = 0
        var heartRate: Double?
        var warnings: [String] = []

        func record(_ message: String) {
            lock.lock(); warnings.append(message); lock.unlock()
        }

        group.enter()
        cumulativeQuantity(.activeEnergyBurned, unit: .kilocalorie(), start: start, end: end) { value, error in
            if let error { record("Active energy: \(error.localizedDescription)") }
            lock.lock(); activeCalories = value ?? 0; lock.unlock(); group.leave()
        }

        group.enter()
        cumulativeQuantity(.stepCount, unit: .count(), start: start, end: end) { value, error in
            if let error { record("Steps: \(error.localizedDescription)") }
            lock.lock(); steps = value ?? 0; lock.unlock(); group.leave()
        }

        group.enter()
        totalWorkoutMinutes(start: start, end: end) { value, error in
            if let error { record("Workouts: \(error.localizedDescription)") }
            lock.lock(); workoutMinutes = value ?? 0; lock.unlock(); group.leave()
        }

        group.enter()
        latestQuantity(.heartRate, unit: HKUnit.count().unitDivided(by: .minute()), start: start, end: end) { value, error in
            if let error { record("Heart rate: \(error.localizedDescription)") }
            lock.lock(); heartRate = value; lock.unlock(); group.leave()
        }

        group.notify(queue: .main) {
            completion(BiteLogHealthSnapshot(
                date: Self.dayString(start),
                activeCalories: Int(activeCalories.rounded()),
                steps: Int(steps.rounded()),
                workoutMinutes: Int(workoutMinutes.rounded()),
                latestHeartRate: heartRate.map { Int($0.rounded()) },
                warnings: warnings
            ))
        }
    }

    private func cumulativeQuantity(
        _ identifier: HKQuantityTypeIdentifier,
        unit: HKUnit,
        start: Date,
        end: Date,
        completion: @escaping (Double?, Error?) -> Void
    ) {
        guard let type = HKQuantityType.quantityType(forIdentifier: identifier) else {
            completion(0, nil); return
        }
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: [])
        let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            completion(result?.sumQuantity()?.doubleValue(for: unit) ?? 0, error)
        }
        store.execute(query)
    }

    private func latestQuantity(
        _ identifier: HKQuantityTypeIdentifier,
        unit: HKUnit,
        start: Date,
        end: Date,
        completion: @escaping (Double?, Error?) -> Void
    ) {
        guard let type = HKQuantityType.quantityType(forIdentifier: identifier) else {
            completion(nil, nil); return
        }
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: [])
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(sampleType: type, predicate: predicate, limit: 1, sortDescriptors: [sort]) { _, samples, error in
            let sample = samples?.first as? HKQuantitySample
            completion(sample?.quantity.doubleValue(for: unit), error)
        }
        store.execute(query)
    }

    private func totalWorkoutMinutes(
        start: Date,
        end: Date,
        completion: @escaping (Double?, Error?) -> Void
    ) {
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: [])
        let query = HKSampleQuery(sampleType: HKObjectType.workoutType(), predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
            let seconds = (samples as? [HKWorkout])?.reduce(0) { $0 + $1.duration } ?? 0
            completion(seconds / 60, error)
        }
        store.execute(query)
    }

    private static func dayString(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private static func error(_ message: String) -> NSError {
        NSError(domain: "BiteLog.HealthKit", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}
