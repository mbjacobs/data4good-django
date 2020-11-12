from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import render_to_string

from web.models import Task, Project
# from website.forms import MakeForm

# PDF Parsing
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy import sparse

# Create your views here.

#class MainView(LoginRequiredMixin, View) :
class MainView(TemplateView) :
    def get(self, request):
        return render(request, 'web/home.html')#, ctx)

class ProjectsView(TemplateView) :
    template_name = "web/projects.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_list'] = Project.objects.all();

        if context['project_list'] and context['project_list'] == 'cio4good' :
            template_name = "web/project_cio4good.html"

        return context


# class ProjectDetailView(TemplateView) :
#     # def get(self, request, project):
#     #     # project = request.GET.get('project', False)
#     #     if project and project == 'cio4good' :
#     #         return render(request, "web/project_cio4good.html")
#     template_name = "web/projects.html"

#     def get(self, request, pk) :
#         project = Project.objects.get(id=pk)
#         context = { 'project' : project}

#         if project.name ==  'CIO4Good':
#             return render(request, "web/project_cio4good.html")#, context)
#         if project.name ==  'PDF Parsing':
#             if request.method == 'GET':
#                 print(request.GET)
#                 return render(request, "web/project_pdfparsing.html")#, context)

#             elif request.method == 'POST':
#                 print(request.POST)
#                 return render(request, "web/project_pdfparsing.html")

#         return render(request, self.template_name, context)

class CIO4GoodView(TemplateView) :
    def get(self, request) :
        return render(request, "web/project_cio4good.html")#, context)



class PDFParsingView(TemplateView) :
    template_name = "web/projects.html"

    def get(self, request) :
        if request.method == 'GET':
            # Debug
            print(request.GET)

            # Define argument dictionary with empty list of PDF search results
            args= {}
            args['search_results'] = []
            
            # Prepare dataframes
            df_pdfs = pd.read_csv('d4g_doc_final.csv')
            df_queries = pd.read_csv('d4g_query.csv')
            df_queries['Query']=df_queries['Query'].replace('', np.nan)

            # Extract summaries from PDFs and queries from query list
            summaries = [x for x in df_pdfs.summary]
            queries = [x for x in df_queries.Query]

            vectorizer = TfidfVectorizer()
            class BM25(object):
                def __init__(self, b=0.75, k1=1.6):
                    self.vectorizer = TfidfVectorizer(norm=None, smooth_idf=False)
                    self.b = b
                    self.k1 = k1

                def fit(self, X):
                    """ Fit IDF to documents X """
                    self.vectorizer.fit(X)
                    y = super(TfidfVectorizer, self.vectorizer).transform(X)
                    self.avdl = y.sum(1).mean()

                def transform(self, q, X):
                    """ Calculate BM25 between query q and documents X """
                    b, k1, avdl = self.b, self.k1, self.avdl

                    # apply CountVectorizer
                    X = super(TfidfVectorizer, self.vectorizer).transform(X)
                    len_X = X.sum(1).A1
                    q, = super(TfidfVectorizer, self.vectorizer).transform([q])
                    assert sparse.isspmatrix_csr(q)

                    # convert to csc for better column slicing
                    X = X.tocsc()[:, q.indices]
                    denom = X + (k1 * (1 - b + b * len_X / avdl))[:, None]
                    idf = self.vectorizer._tfidf.idf_[None, q.indices] - 1.
                    numer = X.multiply(np.broadcast_to(idf, X.shape)) * (k1 + 1)                                                          
                    return (numer / denom).sum(1).A1

            bm25 = BM25()
            bm25.fit(summaries)
            query_sample = bm25.transform(queries[6], summaries)

            weights = []
            for i in query_sample:
                if i > 1:
                    weights.append(i)

            sorted_top = sorted(weights, key = lambda x: x, reverse = True)[:10]

            # Debug
            print(sorted_top)

            sorted_top_i = [np.where(query_sample == i) for i in sorted_top]
            top_indexes = [x[0][0] for x in sorted_top_i]

            # Debug
            print('Query: ' + str(queries[5]) + '\n')

            for i in top_indexes:
                # Create a new PDF dictionary and add it to the list of search results
                pdf = {
                    "title": str(df_pdfs.Title[i]),
                    "summary": str(df_pdfs.summary[i])[:750] + "...", # Truncate summary after 750 characters
                    "link": str(df_pdfs.URL[i])
                }
                args['search_results'].append(pdf)
            
            return render(request, "web/project_pdfparsing.html", args)

        elif request.method == 'POST':
            print(request.POST)

            return render(request, "web/project_pdfparsing.html", args)


class DataSetsView(TemplateView) :
    def get(self, request):
        return render(request, 'web/datasets.html')#, ctx)

class ContributeView(TemplateView) :
    template_name = "web/contribute.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_list'] = Task.objects.all();
        return context

class OrganizationView(TemplateView) :
    def get(self, request):
        return render(request, 'web/organization.html')#, ctx)

class FAQView(TemplateView) :
    def get(self, request):
        return render(request, 'web/faq.html')#, ctx)