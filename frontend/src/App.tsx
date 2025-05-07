import React, {useState} from 'react';
import MatchRadar from './components/MatchRadar';
import WeightSliders from './components/WeightSliders';
import classNames from 'classnames';

interface Recommendation {
    score: number;
    case_name: string;
    application_scenarios: string;
    technology_stack: string[];
    city_size: string;
    budget_range: number[];
    match_reasons: string[];
    match_breakdown: {
        [key: string]: number; // e.g. { "tech": 0.8, "budget": 1, "latency": 0.6 }
    };
}

function App() {
    const [formData, setFormData] = useState({
        applicationScenarios: '',
        tps: 1000,
        latency: 200,
        securityLevel: 'high',
        technologyStack: 'Hyperledger, IPFS',
        citySize: 'large',
        budgetRange: '[500000, 1000000]'
    });
    const [weights, setWeights] = useState({
        scenario: 0.2,
        tech_req: 0.2,
        tech_stack: 0.2,
        city_size: 0.2,
        budget: 0.2,
    });


    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const {name, value} = e.target;

        setFormData(prev => ({
            ...prev,
            [name]: name === 'tps' || name === 'latency'
                ? Number(value)
                : value
        }));
    };

    const scenarioTags = [
        "Energy Grid",
        "Insurance",
        "Healthcare",
        "Tourism",
        "Supply Chain",
        "Logistics",
        "Smart Traffic",
        "Land Registry"
    ];

// 内部 state（你已有的 formData 不用改）
    const [selectedTags, setSelectedTags] = useState<string[]>([]);

// 新增处理函数
    const toggleTag = (tag: string) => {
        setSelectedTags((prev) => {
            const updated = prev.includes(tag)
                ? prev.filter((t) => t !== tag)
                : [...prev, tag];

            // 同步更新到 formData
            setFormData((prevForm) => ({
                ...prevForm,
                applicationScenarios: updated.join(", ")
            }));

            return updated;
        });
    };

    const handleAnalyze = async () => {
        setIsLoading(true);
        setError('');

        try {
            const payload = {
                applicationScenarios: formData.applicationScenarios,
                technicalRequirements: JSON.stringify({
                    tps: formData.tps,
                    latency: formData.latency,
                    security_level: formData.securityLevel
                }),
                technologyStack: formData.technologyStack,
                citySize: formData.citySize,
                budgetRange: formData.budgetRange,

                weights: weights
            };

            const response = await fetch("http://localhost:8000/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Analysis failed');

            const result = await response.json();

            const validatedRecs = result.recommendations.map((rec: any) => ({
                ...rec,
                budget_range: Array.isArray(rec.budget_range)
                    ? rec.budget_range.map(Number)
                    : [0, 0],
                score: Number(rec.score) || 0
            }));

            setRecommendations(validatedRecs);

            const submissionId = result.submission_id;
            const link = document.createElement('a');
            link.href = `http://localhost:8000/download_pdf/${submissionId}`;
            link.download = `report_${submissionId}.pdf`;
            link.click();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Analysis failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
                {/* 左侧表单区域 */}
                <div className="bg-white p-8 rounded-2xl shadow">
                    <h2 className="text-2xl font-bold mb-6 text-center">CityChain Advisor</h2>

                    {error && <div className="mb-4 text-red-500">{error}</div>}

                    <div className="space-y-6">
                        {/* 应用场景 */}
                        <div>
                            <label className="block mb-2 font-medium">Application Scenarios</label>
                            <div className="flex flex-wrap gap-2 mb-3">
                                {scenarioTags.map((tag) => (
                                    <button
                                        key={tag}
                                        type="button"
                                        className={classNames(
                                            "px-4 py-2 rounded-full text-sm transition-all",
                                            selectedTags.includes(tag)
                                                ? "bg-green-500 text-white"
                                                : "bg-gray-100 hover:bg-gray-200"
                                        )}
                                        onClick={() => toggleTag(tag)}
                                    >
                                        {tag}
                                    </button>
                                ))}
                            </div>
                            <textarea
                                name="applicationScenarios"
                                value={formData.applicationScenarios}
                                onChange={handleChange}
                                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                placeholder="Describe your application scenarios..."
                                rows={3}
                            />
                        </div>

                        {/* 技术需求 */}
                        <div className="grid grid-cols-2 gap-6">
                            <div>
                                <label className="block mb-2 font-medium">TPS</label>
                                <input
                                    type="number"
                                    name="tps"
                                    value={formData.tps}
                                    onChange={handleChange}
                                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                    min="1"
                                />
                            </div>
                            <div>
                                <label className="block mb-2 font-medium">Latency (ms)</label>
                                <input
                                    type="number"
                                    name="latency"
                                    value={formData.latency}
                                    onChange={handleChange}
                                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                    min="1"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="block mb-2 font-medium">Security Level</label>
                                <select
                                    name="securityLevel"
                                    value={formData.securityLevel}
                                    onChange={handleChange}
                                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                >
                                    <option value="high">High</option>
                                    <option value="medium">Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                        </div>

                        {/* 技术栈和城市规模 */}
                        <div className="grid grid-cols-2 gap-6">
                            <div>
                                <label className="block mb-2 font-medium">Technology Stack</label>
                                <input
                                    name="technologyStack"
                                    value={formData.technologyStack}
                                    onChange={handleChange}
                                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                />
                            </div>
                            <div>
                                <label className="block mb-2 font-medium">City Size</label>
                                <select
                                    name="citySize"
                                    value={formData.citySize}
                                    onChange={handleChange}
                                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                                >
                                    <option value="small">Small</option>
                                    <option value="medium">Medium</option>
                                    <option value="large">Large</option>
                                </select>
                            </div>
                        </div>

                        {/* 预算范围 */}
                        <div>
                            <label className="block mb-2 font-medium">Budget Range</label>
                            <input
                                name="budgetRange"
                                value={formData.budgetRange}
                                onChange={handleChange}
                                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                            />
                        </div>

                        {/* 权重调节器 */}
                        <div className="pt-4">
                            <h4 className="text-lg font-medium mb-4">Adjust Match Weights</h4>
                            <WeightSliders weights={weights} onChange={setWeights}/>
                        </div>

                        {/* 分析按钮 */}
                        <button
                            onClick={handleAnalyze}
                            disabled={isLoading}
                            className="w-full bg-green-500 text-white px-6 py-3 rounded-lg
                                     hover:bg-green-600 transition-all disabled:bg-gray-400
                                     text-lg font-semibold"
                        >
                            {isLoading ? 'Analyzing...' : 'Start Analysis'}
                        </button>
                    </div>
                </div>

                {/* 右侧推荐结果 */}
                {recommendations.length > 0 && (
                    <div className="lg:sticky lg:top-8 h-fit max-h-[calc(100vh-4rem)] overflow-y-auto">
                        <div className="bg-white p-6 rounded-2xl shadow">
                            <h3 className="text-xl font-semibold mb-6">Recommendations</h3>
                            <div className="space-y-6">
                                {recommendations.map((rec, index) => (
                                    <div key={index} className="p-4 bg-gray-50 rounded-lg">
                                        {/* 保持原有推荐结果内容不变 */}
                                        <div className="flex justify-between items-start mb-3">
                                            <h4 className="font-medium text-lg">{rec.case_name}</h4>
                                            <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded">
                                                Score: {rec.score.toFixed(2)}
                                            </span>
                                        </div>
                                        <p className="text-sm mb-3 text-gray-600">{rec.application_scenarios}</p>
                                        <div className="text-sm space-y-2">
                                            <div>📍 City Size: {rec.city_size}</div>
                                            <div>💰 Budget: ${rec.budget_range[0].toLocaleString()} -
                                                ${rec.budget_range[1].toLocaleString()}</div>
                                            <div>🛠 Technologies: {rec.technology_stack.join(', ')}</div>
                                            <div className="mt-3 text-green-600 font-medium">
                                                {rec.match_reasons.join(' • ')}
                                            </div>
                                        </div>
                                        {rec.match_breakdown && (
                                            <div className="mt-4">
                                                <MatchRadar
                                                    scores={Object.entries(rec.match_breakdown).map(([key, value]) => ({
                                                        metric: key,
                                                        value: value
                                                    }))}
                                                />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;

//     return (
//         <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
//             <div className="w-full max-w-xl p-6 bg-white rounded-2xl shadow">
//                 <h2 className="text-2xl font-bold mb-4 text-center">CityChain Advisor</h2>
//
//                 {error && <div className="mb-4 text-red-500">{error}</div>}
//
//                 <div className="space-y-4">
//                     <div>
//                         <label className="block mb-1 font-medium">Application Scenarios</label>
//                         <div className="flex flex-wrap gap-2 mb-2">
//                             {scenarioTags.map((tag) => (
//                                 <button
//                                     key={tag}
//                                     type="button"
//                                     className={classNames(
//                                         "px-3 py-1 text-sm rounded-none border transition",
//                                         selectedTags.includes(tag)
//                                             ? "bg-green-500 text-white border-green-600"
//                                             : "bg-gray-100 text-gray-800 border-gray-300 hover:bg-green-100"
//                                     )}
//
//                                     onClick={() => toggleTag(tag)}
//                                 >
//                                     {tag}
//                                 </button>
//                             ))}
//                         </div>
//
//                         {/* Free-form textarea */}
//                         <textarea
//                             name="applicationScenarios"
//                             value={formData.applicationScenarios}
//                             onChange={handleChange}
//                             className="w-full p-2 border rounded"
//                             placeholder="Describe your application scenarios or select from tags..."
//                             rows={4}
//                         />
//                     </div>
//
//                     <div>
//                         <label className="block mb-1 font-medium">Technical Requirements</label>
//
//                         <div className="grid grid-cols-2 gap-4 mb-3">
//                             <div>
//                                 <label className="block text-sm mb-1">TPS</label>
//                                 <input
//                                     type="number"
//                                     name="tps"
//                                     value={formData.tps}
//                                     onChange={handleChange}
//                                     className="w-full p-2 border rounded"
//                                     min="1"
//                                 />
//                             </div>
//
//                             <div>
//                                 <label className="block text-sm mb-1">Latency (ms)</label>
//                                 <input
//                                     type="number"
//                                     name="latency"
//                                     value={formData.latency}
//                                     onChange={handleChange}
//                                     className="w-full p-2 border rounded"
//                                     min="1"
//                                 />
//                             </div>
//                         </div>
//
//                         <div>
//                             <label className="block text-sm mb-1">Security Level</label>
//                             <select
//                                 name="securityLevel"
//                                 value={formData.securityLevel}
//                                 onChange={handleChange}
//                                 className="w-full p-2 border rounded"
//                             >
//                                 <option value="high">High</option>
//                                 <option value="medium">Medium</option>
//                                 <option value="low">Low</option>
//                             </select>
//                         </div>
//                     </div>
//
//                     <div>
//                         <label className="block mb-1 font-medium">
//                             Technology Stack (comma-separated)
//                             <span className="text-sm text-gray-500 ml-2">e.g. Hyperledger, IPFS, Solidity</span>
//                         </label>
//                         <input
//                             name="technologyStack"
//                             value={formData.technologyStack}
//                             onChange={handleChange}
//                             className="w-full p-2 border rounded"
//                         />
//                     </div>
//
//                     <div>
//                         <label className="block mb-1 font-medium">City Size</label>
//                         <select
//                             name="citySize"
//                             value={formData.citySize}
//                             onChange={handleChange}
//                             className="w-full p-2 border rounded"
//                         >
//                             <option value="small">Small</option>
//                             <option value="medium">Medium</option>
//                             <option value="large">Large</option>
//                         </select>
//                     </div>
//
//                     <div>
//                         <label className="block mb-1 font-medium">
//                             Budget Range (JSON array)
//                             <span className="text-sm text-gray-500 ml-2">e.g. [500000, 1000000]</span>
//                         </label>
//                         <input
//                             name="budgetRange"
//                             value={formData.budgetRange}
//                             onChange={handleChange}
//                             className="w-full p-2 border rounded"
//                         />
//                     </div>
//                 </div>
//
//                 <div className="mt-6">
//                     <h4 className="font-medium mb-2">Adjust Match Weights</h4>
//                     <WeightSliders weights={weights} onChange={setWeights}/>
//                 </div>
//
//                 <button
//                     onClick={handleAnalyze}
//                     disabled={isLoading}
//                     className="mt-6 bg-green-500 text-white px-4 py-2 rounded w-full hover:bg-green-600 disabled:bg-gray-400"
//                 >
//                     {isLoading ? 'Analyzing...' : 'Analyze'}
//                 </button>
//
//                 {recommendations.length > 0 && (
//                     <div className="mt-8">
//                         <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
//                         <div className="space-y-4">
//                             {recommendations.map((rec, index) => (
//                                 <div key={index} className="p-4 bg-gray-50 rounded-lg">
//                                     <div className="flex justify-between items-start mb-2">
//                                         <h4 className="font-medium">{rec.case_name}</h4>
//                                         <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
//                       {/*Score: {rec.score}*/}
//                                             Score: {rec.score.toFixed(2)}
//                     </span>
//                                     </div>
//                                     <p className="text-sm mb-2">{rec.application_scenarios}</p>
//                                     <div className="text-sm space-y-1">
//                                         <div>📍 City Size: {rec.city_size}</div>
//                                         <div>💰 Budget: ${rec.budget_range[0].toLocaleString()} -
//                                             ${rec.budget_range[1].toLocaleString()}</div>
//                                         <div>🛠 Technologies: {rec.technology_stack.join(', ')}</div>
//                                         <div className="mt-2 text-green-600">
//                                             {rec.match_reasons.join(' • ')}
//                                         </div>
//                                     </div>
//
//                                     {rec.match_breakdown && (
//                                         <div className="mt-4">
//                                             <MatchRadar
//                                                 scores={Object.entries(rec.match_breakdown).map(([key, value]) => ({
//                                                     metric: key,
//                                                     value: value
//                                                 }))}
//                                             />
//                                         </div>
//                                     )}
//
//
//                                 </div>
//                             ))}
//                         </div>
//                     </div>
//                 )}
//             </div>
//         </div>
//     );
// }
//
// export default App;