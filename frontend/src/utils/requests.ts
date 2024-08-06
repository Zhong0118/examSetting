import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class HttpRequest {
    private readonly baseUrl: string;
    private axiosInstance: AxiosInstance;

    constructor() {
        this.baseUrl = 'http://localhost:5000';
        this.axiosInstance = axios.create({
            baseURL: this.baseUrl,
            timeout: 80000,
            withCredentials: true,
        });

        this.interceptors();
    }

    // 请求拦截
    private interceptors() {
        this.axiosInstance.interceptors.request.use(config => {
            return config;
        }, error => {
            return Promise.reject(error);
        });

        this.axiosInstance.interceptors.response.use(response => {
            // 处理返回的数据
            console.log('返回数据处理', response.data);
            return response;
        }, error => {
            console.error('error==>', error);
            return Promise.reject(error);
        });
    }

    request(options: AxiosRequestConfig) {
        return this.axiosInstance(options);
    }
}

const http = new HttpRequest();
export default http;