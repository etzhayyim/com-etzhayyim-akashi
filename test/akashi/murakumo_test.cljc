(ns akashi.murakumo-test
  (:require [clojure.test :refer [deftest is testing]]
            [akashi.murakumo :as akashi]))

(def full-attestations
  {:council-charter-attestation "tx-council"
   :source-policy-review "tx-source-policy"
   :akashi-r1-activation "tx-r1"
   :landing-fetch-rate-limit-review "tx-landing"
   :malak-bridge-review "tx-malak"})

(deftest maps-all-legacy-akashi-cells
  (is (= #{"akashi_cross_platform_link"
           "akashi_disclosure_fetch"
           "akashi_landing_evidence"
           "akashi_malak_evidence_bridge"
           "akashi_normalize_creative"
           "akashi_source_registry"
           "akashi_transparency_report"}
         (set (map :legacy-cell (vals akashi/cell-specs))))))

(deftest r0-gates-block-effects
  (let [plan (akashi/cell-plan :disclosure-fetch
                               {:source-id "meta-ad-library"
                                :computed-at "2026-06-29T00:00:00Z"})]
    (is (= :blocked (:status plan)))
    (is (= akashi/common-gates (:missing-gates plan)))
    (is (empty? (:effects plan)))))

(deftest attested-source-registry-emits-mst-effect
  (let [plan (akashi/cell-plan :source-registry
                               {:attestations full-attestations
                                :source-id "meta-ad-library"
                                :computed-at "2026-06-29T00:00:00Z"
                                :record {:sourceUrl "https://example.test/policy"
                                         :collectionStatus "disabled"}})
        effect (first (:effects plan))]
    (is (= :ready (:status plan)))
    (is (= :mst/put-record (:op effect)))
    (is (= akashi/actor-did (:actor effect)))
    (is (= "com.etzhayyim.akashi.sourcePolicySnapshot" (:collection effect)))
    (is (= "meta-ad-library" (:rkey effect)))
    (is (= "https://example.test/policy" (get-in effect [:record :sourceUrl])))))

(deftest normalize-creative-plans-three-records
  (let [plan (akashi/cell-plan :normalize-creative
                               {:attestations full-attestations
                                :source-id "creative-1"
                                :computed-at "2026-06-29T00:00:00Z"
                                :records {"com.etzhayyim.akashi.creativeDisclosure"
                                          {:creativeText "public disclosure text"}}})]
    (is (= :ready (:status plan)))
    (is (= ["com.etzhayyim.akashi.advertiserIdentity"
            "com.etzhayyim.akashi.creativeDisclosure"
            "com.etzhayyim.akashi.deliveryDisclosure"]
           (mapv :collection (:effects plan))))
    (is (= "public disclosure text"
           (get-in plan [:records 1 :record :creativeText])))))

(deftest special-gates-remain-cell-specific
  (testing "landing evidence requires landing review"
    (let [attestations (dissoc full-attestations :landing-fetch-rate-limit-review)
          plan (akashi/cell-plan :landing-evidence {:attestations attestations})]
      (is (= [:landing-fetch-rate-limit-review] (:missing-gates plan)))
      (is (empty? (:effects plan)))))
  (testing "malak bridge requires malak review"
    (let [attestations (dissoc full-attestations :malak-bridge-review)
          plan (akashi/cell-plan :malak-evidence-bridge {:attestations attestations})]
      (is (= [:malak-bridge-review] (:missing-gates plan)))
      (is (empty? (:effects plan))))))

(deftest all-cell-plans-ready-when-attested
  (let [plans (akashi/all-cell-plans {:attestations full-attestations
                                      :source-id "meta-ad-library"
                                      :computed-at "2026-06-29T00:00:00Z"})]
    (is (= (set (keys akashi/cell-specs)) (set (keys plans))))
    (is (every? #(= :ready (:status %)) (vals plans)))
    (is (= 9 (count (mapcat :effects (vals plans)))))
    (is (every? #(= true (get-in % [:record :nonAdjudicatingNotice]))
                (mapcat :effects (vals plans))))))
